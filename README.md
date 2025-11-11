# Padel Court Availability Checker

Automated script that checks for available padel court slots and sends Telegram notifications when 3 consecutive 30-minute slots are found between 18:00 and 21:00.

## Features

- 🔍 Scrapes the ActiveZone API for available court slots
- ⏰ Finds 3 consecutive 30-minute time slots (90 minutes total)
- 🕐 Checks time range: 18:00 - 21:00
- 📱 Sends Telegram notifications when slots are found
- 🐳 Dockerized for easy deployment
- ☁️ Ready for GCP Cloud Run with Cloud Scheduler

## Prerequisites

### 1. Telegram Bot Setup

1. Create a Telegram bot:
   - Message [@BotFather](https://t.me/botfather) on Telegram
   - Send `/newbot` and follow instructions
   - Save your `BOT_TOKEN`

2. Get your Chat ID:
   - Message [@userinfobot](https://t.me/userinfobot) on Telegram
   - Save your `Chat ID`

### 2. Google Cloud Platform Account

- Enable billing on your GCP account
- Install [Google Cloud SDK](https://cloud.google.com/sdk/docs/install)

## Local Testing

### 1. Setup Environment

```bash
# Copy environment template
cp .env.example .env

# Edit .env with your credentials
nano .env
```

### 2. Test with Docker Compose

```bash
# Build and run
docker-compose up --build

# Or run in background
docker-compose up -d

# View logs
docker-compose logs -f
```

### 3. Test without Docker

```bash
# Install dependencies
pip install -r requirements.txt

# Set environment variables
export TELEGRAM_BOT_TOKEN="your_token"
export TELEGRAM_CHAT_ID="your_chat_id"

# Run script
python padel_checker.py
```

## GCP Deployment (Recommended)

### Method 1: Cloud Run + Cloud Scheduler (Best for every 5 minutes)

#### Step 1: Setup GCP Project

```bash
# Set your project ID
export PROJECT_ID="your-project-id"
export REGION="europe-west1"  # Choose closest region

# Set project
gcloud config set project $PROJECT_ID

# Enable required APIs
gcloud services enable run.googleapis.com
gcloud services enable cloudscheduler.googleapis.com
gcloud services enable cloudbuild.googleapis.com
```

#### Step 2: Build and Deploy to Cloud Run

```bash
# Build the container
gcloud builds submit --tag gcr.io/$PROJECT_ID/padel-checker

# Deploy to Cloud Run (will NOT run automatically)
gcloud run deploy padel-checker \
  --image gcr.io/$PROJECT_ID/padel-checker \
  --platform managed \
  --region $REGION \
  --no-allow-unauthenticated \
  --set-env-vars TELEGRAM_BOT_TOKEN="YOUR_TOKEN" \
  --set-env-vars TELEGRAM_CHAT_ID="YOUR_CHAT_ID" \
  --set-env-vars LOCATION_ID="224" \
  --set-env-vars DAYS_TO_CHECK="7" \
  --memory 256Mi \
  --cpu 1 \
  --timeout 300 \
  --max-instances 1
```

**Important:** Replace `YOUR_TOKEN` and `YOUR_CHAT_ID` with your actual credentials!

#### Step 3: Create Cloud Scheduler Job (Runs every 5 minutes)

```bash
# Get the Cloud Run service URL
SERVICE_URL=$(gcloud run services describe padel-checker \
  --platform managed \
  --region $REGION \
  --format 'value(status.url)')

# Create service account for scheduler
gcloud iam service-accounts create padel-checker-scheduler \
  --display-name "Padel Checker Scheduler"

# Grant permission to invoke Cloud Run
gcloud run services add-iam-policy-binding padel-checker \
  --region=$REGION \
  --member=serviceAccount:padel-checker-scheduler@$PROJECT_ID.iam.gserviceaccount.com \
  --role=roles/run.invoker

# Create scheduler job (runs every 5 minutes)
gcloud scheduler jobs create http padel-checker-job \
  --location=$REGION \
  --schedule="*/5 * * * *" \
  --uri="$SERVICE_URL" \
  --http-method=POST \
  --oidc-service-account-email=padel-checker-scheduler@$PROJECT_ID.iam.gserviceaccount.com \
  --oidc-token-audience="$SERVICE_URL"
```

#### Step 4: Test the Scheduler

```bash
# Manually trigger the job to test
gcloud scheduler jobs run padel-checker-job --location=$REGION

# Check logs
gcloud run services logs read padel-checker --region=$REGION --limit 50
```

### Method 2: Using Secrets Manager (More Secure)

For production, use Secret Manager instead of environment variables:

```bash
# Enable Secret Manager API
gcloud services enable secretmanager.googleapis.com

# Create secrets
echo -n "YOUR_BOT_TOKEN" | gcloud secrets create telegram-bot-token --data-file=-
echo -n "YOUR_CHAT_ID" | gcloud secrets create telegram-chat-id --data-file=-

# Grant access to Cloud Run service account
PROJECT_NUMBER=$(gcloud projects describe $PROJECT_ID --format="value(projectNumber)")

gcloud secrets add-iam-policy-binding telegram-bot-token \
  --member=serviceAccount:$PROJECT_NUMBER-compute@developer.gserviceaccount.com \
  --role=roles/secretmanager.secretAccessor

gcloud secrets add-iam-policy-binding telegram-chat-id \
  --member=serviceAccount:$PROJECT_NUMBER-compute@developer.gserviceaccount.com \
  --role=roles/secretmanager.secretAccessor

# Deploy with secrets
gcloud run deploy padel-checker \
  --image gcr.io/$PROJECT_ID/padel-checker \
  --platform managed \
  --region $REGION \
  --no-allow-unauthenticated \
  --set-secrets TELEGRAM_BOT_TOKEN=telegram-bot-token:latest \
  --set-secrets TELEGRAM_CHAT_ID=telegram-chat-id:latest \
  --set-env-vars LOCATION_ID="224" \
  --set-env-vars DAYS_TO_CHECK="7" \
  --memory 256Mi \
  --cpu 1 \
  --timeout 300 \
  --max-instances 1
```

## Configuration

### Environment Variables

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `TELEGRAM_BOT_TOKEN` | Your Telegram bot token | - | Yes |
| `TELEGRAM_CHAT_ID` | Your Telegram chat ID | - | Yes |
| `LOCATION_ID` | Court location ID from API | 224 | No |
| `DAYS_TO_CHECK` | Number of days to check ahead | 7 | No |

### Customization

To modify the script behavior, edit `padel_checker.py`:

- **Time range**: Change lines with `target_start` and `target_end`
- **Number of consecutive slots**: Modify `if len(group) == 3:`
- **Slot duration**: Adjust logic in `find_consecutive_slots()`

## Monitoring

### View Logs

```bash
# Cloud Run logs
gcloud run services logs read padel-checker --region=$REGION --limit 100

# Scheduler logs
gcloud scheduler jobs describe padel-checker-job --location=$REGION
```

### Check Scheduler Status

```bash
# List all jobs
gcloud scheduler jobs list --location=$REGION

# Pause the job
gcloud scheduler jobs pause padel-checker-job --location=$REGION

# Resume the job
gcloud scheduler jobs resume padel-checker-job --location=$REGION
```

## Cost Estimation

GCP Cloud Run + Cloud Scheduler is very cost-effective:

- **Cloud Run**: ~$0.01-0.05/month (with free tier)
- **Cloud Scheduler**: ~$0.10/month (3 free jobs, then $0.10/job)
- **Total**: ~$0.10-0.15/month

Running every 5 minutes = 8,640 executions/month (well within free tier limits)

## Troubleshooting

### No messages received?

1. Check Cloud Run logs:
   ```bash
   gcloud run services logs read padel-checker --region=$REGION --limit 50
   ```

2. Verify Telegram credentials:
   ```bash
   curl https://api.telegram.org/bot<YOUR_TOKEN>/getMe
   ```

3. Test manually:
   ```bash
   gcloud scheduler jobs run padel-checker-job --location=$REGION
   ```

### Scheduler not triggering?

1. Check scheduler status:
   ```bash
   gcloud scheduler jobs describe padel-checker-job --location=$REGION
   ```

2. Verify service account permissions:
   ```bash
   gcloud run services get-iam-policy padel-checker --region=$REGION
   ```

## Updating the Application

```bash
# Rebuild and redeploy
gcloud builds submit --tag gcr.io/$PROJECT_ID/padel-checker
gcloud run deploy padel-checker \
  --image gcr.io/$PROJECT_ID/padel-checker \
  --region $REGION
```

## Cleanup

To remove all resources:

```bash
# Delete Cloud Run service
gcloud run services delete padel-checker --region=$REGION

# Delete Cloud Scheduler job
gcloud scheduler jobs delete padel-checker-job --location=$REGION

# Delete service account
gcloud iam service-accounts delete \
  padel-checker-scheduler@$PROJECT_ID.iam.gserviceaccount.com

# Delete container image
gcloud container images delete gcr.io/$PROJECT_ID/padel-checker
```

## Support

If you encounter issues:
1. Check the logs first
2. Verify your Telegram bot token and chat ID
3. Ensure GCP APIs are enabled
4. Check that the API endpoint is accessible

## License

MIT
