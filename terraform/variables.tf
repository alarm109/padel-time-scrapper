variable "project_id" {
  description = "GCP Project ID"
  type        = string
}

variable "region" {
  description = "GCP region for Cloud Run and Cloud Scheduler"
  type        = string
  default     = "europe-west1"
}

variable "telegram_bot_token" {
  description = "Telegram Bot Token"
  type        = string
  sensitive   = true
}

variable "telegram_chat_id" {
  description = "Telegram Chat ID"
  type        = string
  sensitive   = true
}

variable "location_id" {
  description = "Court location ID from API"
  type        = string
  default     = "224"
}

variable "days_to_check" {
  description = "Number of days to check ahead"
  type        = number
  default     = 7
}

variable "day_delay" {
  description = "Number to delay days to start from"
  type        = number
  default     = 1
}

variable "ticket_from" {
  description = "Hours to start the search from"
  type        = string
  default     = "18:00"
}

variable "ticket_to" {
  description = "Hours till check the search"
  type        = string
  default     = "20:30"
}

variable "schedule" {
  description = "Cron schedule for Cloud Scheduler (runs every 5 minutes by default)"
  type        = string
  default     = "*/5 * * * *"
}

variable "time_zone" {
  description = "Time zone for Cloud Scheduler"
  type        = string
  default     = "Europe/Vilnius"
}

variable "use_secret_manager" {
  description = "Use Secret Manager for sensitive data (more secure)"
  type        = bool
  default     = true
}
