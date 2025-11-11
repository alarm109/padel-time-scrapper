# GCP Configuration
project_id = "padel-time-scrapper"
region     = "europe-west1"  # Choose your preferred region

# Telegram Configuration (REQUIRED - Replace with your actual values)
telegram_bot_token = "7087560098:AAGqa8uJmJ7i8ot2j8tiXUxt3eBwXaaeqTo"
telegram_chat_id   = "6772347030"

# API Configuration (Optional)
location_id = "224"
days_to_check = 30
day_delay = 1
ticket_from = "18:00"
ticket_to = "20:30"

# Scheduler Configuration (Optional)
schedule  = "*/5 * * * *"      # Every 5 minutes
time_zone = "Europe/Vilnius"   # Change to your timezone

# Security Configuration (Optional)
use_secret_manager = true  # Set to false to use env vars instead of Secret Manager
