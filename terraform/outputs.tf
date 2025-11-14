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

output "state_bucket_name" {
  description = "GCS bucket name for storing state"
  value       = google_storage_bucket.state_bucket.name
}

output "view_state_command" {
  description = "Command to view the current state file"
  value       = "gsutil cat gs://${google_storage_bucket.state_bucket.name}/padel_state.json"
}
