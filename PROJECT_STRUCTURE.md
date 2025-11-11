# Padel Court Checker - Project Structure

```
padel-court-checker/
├── padel_checker.py       # Main Python script
├── requirements.txt       # Python dependencies
├── Dockerfile            # Container configuration
├── docker-compose.yml    # Local testing setup
├── deploy.sh            # Automated GCP deployment script (executable)
├── .env.example         # Environment variables template
├── .gitignore          # Git ignore rules
├── README.md           # Full documentation
└── QUICKSTART.md       # Quick setup guide
```

## 📋 File Descriptions

### Core Application
- **padel_checker.py**: Main script that:
  - Fetches available time slots from the API
  - Finds 3 consecutive 30-minute slots between 18:00-21:00
  - Sends Telegram notifications for new findings
  - Prevents duplicate notifications

### Docker & Deployment
- **Dockerfile**: Builds a lightweight Python 3.11 container
- **docker-compose.yml**: For local testing with Docker
- **deploy.sh**: One-command deployment to GCP (Cloud Run + Cloud Scheduler)

### Configuration
- **.env.example**: Template for environment variables
  - Copy to `.env` for local testing
  - Set in GCP during deployment
- **requirements.txt**: Python package dependencies (requests)

### Documentation
- **README.md**: Complete guide with:
  - Features and prerequisites
  - Local testing instructions
  - Detailed GCP deployment steps
  - Monitoring and troubleshooting
  - Cost estimation
- **QUICKSTART.md**: 5-minute setup guide
- **.gitignore**: Excludes sensitive files and build artifacts

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     GCP Cloud Scheduler                      │
│              (Triggers every 5 minutes)                      │
└─────────────────────┬───────────────────────────────────────┘
                      │
                      ↓
┌─────────────────────────────────────────────────────────────┐
│                      GCP Cloud Run                           │
│  ┌───────────────────────────────────────────────────────┐  │
│  │          Docker Container (padel_checker.py)          │  │
│  │                                                        │  │
│  │  1. Fetch data from API                              │  │
│  │  2. Check for 3 consecutive 30-min slots (18:00-21:00) │
│  │  3. Compare with sent notifications                   │  │
│  │  4. Send new findings via Telegram                    │  │
│  └───────────────────────────────────────────────────────┘  │
└──────────────┬────────────────────────────┬─────────────────┘
               │                            │
               ↓                            ↓
    ┌──────────────────────┐    ┌─────────────────────┐
    │  Activezone.fun API  │    │   Telegram Bot API  │
    │  (Court bookings)    │    │   (Notifications)   │
    └──────────────────────┘    └─────────────────────┘
```

## 🔄 Workflow

1. **Cloud Scheduler** triggers the Cloud Run service every 5 minutes
2. **Cloud Run** starts a container instance
3. **padel_checker.py** executes:
   - Fetches ticket data for the next 7 days
   - Filters for "free" status slots
   - Groups by court and checks for 3 consecutive 30-min slots
   - Validates slots are between 18:00-21:00
   - Checks against previously sent notifications
   - Sends Telegram messages for new findings
4. **Container** shuts down after execution (serverless)

## 🔐 Environment Variables

| Variable | Required | Description | Example |
|----------|----------|-------------|---------|
| `TELEGRAM_BOT_TOKEN` | Yes | Bot token from @BotFather | `123456789:ABCdef...` |
| `TELEGRAM_CHAT_ID` | Yes | Your Telegram chat ID | `123456789` |
| `DAYS_TO_CHECK` | No | Days ahead to check | `7` (default) |

## 🎯 Key Features

✅ **No Duplicates**: Tracks sent notifications to avoid spam
✅ **Serverless**: Only runs when triggered, minimal costs
✅ **Scalable**: Can easily add more locations or time ranges
✅ **Reliable**: GCP infrastructure with automatic retries
✅ **Monitored**: Full logging via Cloud Run logs

## 📦 Dependencies

- Python 3.11
- requests 2.31.0
- Docker (for containerization)
- Google Cloud Platform (for hosting)

## 🚀 Getting Started

See **QUICKSTART.md** for a 5-minute setup guide!
