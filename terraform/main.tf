terraform {
  required_version = ">= 1.0"
  
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
  }
}

provider "google" {
  project = var.project_id
  region  = var.region
}

# Enable required APIs
resource "google_project_service" "run" {
  service = "run.googleapis.com"
  disable_on_destroy = false
}

resource "google_project_service" "scheduler" {
  service = "cloudscheduler.googleapis.com"
  disable_on_destroy = false
}

resource "google_project_service" "build" {
  service = "cloudbuild.googleapis.com"
  disable_on_destroy = false
}

resource "google_project_service" "secretmanager" {
  count = var.use_secret_manager ? 1 : 0
  service = "secretmanager.googleapis.com"
  disable_on_destroy = false
}

# Create secrets in Secret Manager (optional, more secure)
resource "google_secret_manager_secret" "telegram_bot_token" {
  count     = var.use_secret_manager ? 1 : 0
  secret_id = "telegram-bot-token"

  replication {
    auto {}
  }

  depends_on = [google_project_service.secretmanager]
}

resource "google_secret_manager_secret_version" "telegram_bot_token" {
  count  = var.use_secret_manager ? 1 : 0
  secret = google_secret_manager_secret.telegram_bot_token[0].id
  secret_data = var.telegram_bot_token
}

resource "google_secret_manager_secret" "telegram_chat_id" {
  count     = var.use_secret_manager ? 1 : 0
  secret_id = "telegram-chat-id"

  replication {
    auto {}
  }

  depends_on = [google_project_service.secretmanager]
}

resource "google_secret_manager_secret_version" "telegram_chat_id" {
  count  = var.use_secret_manager ? 1 : 0
  secret = google_secret_manager_secret.telegram_chat_id[0].id
  secret_data = var.telegram_chat_id
}

# Build the container image
resource "null_resource" "build_image" {
  triggers = {
    dockerfile_hash = filesha256("${path.module}/../Dockerfile")
    script_hash     = filesha256("${path.module}/../padel_checker.py")
  }

  provisioner "local-exec" {
    working_dir = "${path.module}/.."
    command     = "gcloud builds submit --tag gcr.io/${var.project_id}/padel-checker --project ${var.project_id} ."
  }

  depends_on = [google_project_service.build]
}

# Service account for Cloud Run
resource "google_service_account" "cloudrun" {
  account_id   = "padel-checker-run"
  display_name = "Padel Checker Cloud Run Service Account"
}

# Grant Secret Manager access to Cloud Run service account (if using secrets)
resource "google_secret_manager_secret_iam_member" "bot_token_access" {
  count     = var.use_secret_manager ? 1 : 0
  secret_id = google_secret_manager_secret.telegram_bot_token[0].id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${google_service_account.cloudrun.email}"
}

resource "google_secret_manager_secret_iam_member" "chat_id_access" {
  count     = var.use_secret_manager ? 1 : 0
  secret_id = google_secret_manager_secret.telegram_chat_id[0].id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${google_service_account.cloudrun.email}"
}

# Cloud Run service
resource "google_cloud_run_v2_service" "padel_checker" {
  name     = "padel-checker"
  location = var.region

  template {
    service_account = google_service_account.cloudrun.email

    containers {
      image = "gcr.io/${var.project_id}/padel-checker:latest"

      resources {
        limits = {
          cpu    = "1"
          memory = "256Mi"
        }
      }

      scaling {
        min_instance_count = 0  # Scale to zero when idle
        max_instance_count = 1  # Only need one instance
      }

      # Optional: Set a reasonable timeout
      timeout = "60s"  # More than enough for your 30 requests

      # Environment variables (if not using Secret Manager)
      dynamic "env" {
        for_each = var.use_secret_manager ? [] : [1]
        content {
          name  = "TELEGRAM_BOT_TOKEN"
          value = var.telegram_bot_token
        }
      }

      dynamic "env" {
        for_each = var.use_secret_manager ? [] : [1]
        content {
          name  = "TELEGRAM_CHAT_ID"
          value = var.telegram_chat_id
        }
      }

      # Secrets from Secret Manager (if using)
      dynamic "env" {
        for_each = var.use_secret_manager ? [1] : []
        content {
          name = "TELEGRAM_BOT_TOKEN"
          value_source {
            secret_key_ref {
              secret  = google_secret_manager_secret.telegram_bot_token[0].secret_id
              version = "latest"
            }
          }
        }
      }

      dynamic "env" {
        for_each = var.use_secret_manager ? [1] : []
        content {
          name = "TELEGRAM_CHAT_ID"
          value_source {
            secret_key_ref {
              secret  = google_secret_manager_secret.telegram_chat_id[0].secret_id
              version = "latest"
            }
          }
        }
      }

      env {
        name  = "LOCATION_ID"
        value = var.location_id
      }

      env {
        name  = "DAYS_TO_CHECK"
        value = tostring(var.days_to_check)
      }

      env {
        name  = "DAY_DELAY"
        value = tostring(var.day_delay)
      }

      env {
        name  = "TICKET_TO"
        value = tostring(var.ticket_to)
      }

      env {
        name  = "TICKET_FROM"
        value = tostring(var.ticket_from)
      }
    }

    timeout = "300s"

    scaling {
      max_instance_count = 1
    }
  }

  depends_on = [
    google_project_service.run,
    null_resource.build_image
  ]
}

# Service account for Cloud Scheduler
resource "google_service_account" "scheduler" {
  account_id   = "padel-checker-scheduler"
  display_name = "Padel Checker Scheduler Service Account"
}

# Grant invoker permission to scheduler service account
resource "google_cloud_run_service_iam_member" "scheduler_invoker" {
  location = google_cloud_run_v2_service.padel_checker.location
  service  = google_cloud_run_v2_service.padel_checker.name
  role     = "roles/run.invoker"
  member   = "serviceAccount:${google_service_account.scheduler.email}"
}

# Cloud Scheduler job (runs every 5 minutes)
resource "google_cloud_scheduler_job" "padel_checker" {
  name             = "padel-checker-job"
  description      = "Trigger Padel Checker every 5 minutes"
  schedule         = var.schedule
  time_zone        = var.time_zone
  region           = var.region
  attempt_deadline = "320s"

  retry_config {
    retry_count = 1
  }

  http_target {
    http_method = "POST"
    uri         = google_cloud_run_v2_service.padel_checker.uri

    oidc_token {
      service_account_email = google_service_account.scheduler.email
      audience              = google_cloud_run_v2_service.padel_checker.uri
    }
  }

  depends_on = [
    google_project_service.scheduler,
    google_cloud_run_service_iam_member.scheduler_invoker
  ]
}
