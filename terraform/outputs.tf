output "cloud_run_service_url" {
  description = "URL of the Cloud Run service"
  value       = google_cloud_run_v2_service.padel_checker.uri
}

output "cloud_run_service_name" {
  description = "Name of the Cloud Run service"
  value       = google_cloud_run_v2_service.padel_checker.name
}

output "scheduler_job_name" {
  description = "Name of the Cloud Scheduler job"
  value       = google_cloud_scheduler_job.padel_checker.name
}

output "scheduler_schedule" {
  description = "Schedule of the Cloud Scheduler job"
  value       = google_cloud_scheduler_job.padel_checker.schedule
}

output "region" {
  description = "Deployment region"
  value       = var.region
}

output "view_logs_command" {
  description = "Command to view Cloud Run logs"
  value       = "gcloud run services logs read ${google_cloud_run_v2_service.padel_checker.name} --region=${var.region} --limit=50"
}

output "trigger_job_command" {
  description = "Command to manually trigger the scheduler job"
  value       = "gcloud scheduler jobs run ${google_cloud_scheduler_job.padel_checker.name} --location=${var.region}"
}

output "pause_job_command" {
  description = "Command to pause the scheduler job"
  value       = "gcloud scheduler jobs pause ${google_cloud_scheduler_job.padel_checker.name} --location=${var.region}"
}

output "resume_job_command" {
  description = "Command to resume the scheduler job"
  value       = "gcloud scheduler jobs resume ${google_cloud_scheduler_job.padel_checker.name} --location=${var.region}"
}
