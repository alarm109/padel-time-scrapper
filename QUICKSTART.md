# Quick Start Guide - Padel Court Checker

## 🚀 Fast Setup (5 minutes)

### Step 1: Get Telegram Credentials

1. **Create a Bot**:
   - Open Telegram and search for [@BotFather](https://t.me/botfather)
   - Send `/newbot` and follow instructions
   - Save your **bot token** (looks like: `123456789:ABCdefGHIjklMNOpqrsTUVwxyz`)

2. **Get Your Chat ID**:
   - Search for [@userinfobot](https://t.me/userinfobot) in Telegram
   - Start a chat with it
   - Save your **chat ID** (a number like: `123456789`)

3. **Start Your Bot**:
   - Search for your bot by the username you created
   - Click "START" to activate it

### Step 2: Deploy to GCP (Automated)

```bash
# Make sure you have gcloud CLI installed and authenticated
gcloud auth login

# Run the automated deployment script
./deploy.sh
```

The script will:
- ✅ Ask for your configuration (project ID, Telegram credentials, etc.)
- ✅ Enable required APIs
- ✅ Build and deploy the Docker container
- ✅ Set up Cloud Scheduler to run every 5 minutes
- ✅ Test the deployment

**That's it!** You'll start receiving Telegram notifications when 3 consecutive 30-minute slots become available between 18:00-21:00.

---

## 🧪 Local Testing (Optional)

Before deploying, you can test locally:

1. **Copy environment template**:
```bash
cp .env.example .env
```

2. **Edit `.env` with your credentials**:
```
TELEGRAM_BOT_TOKEN=your_bot_token_here
TELEGRAM_CHAT_ID=your_chat_id_here
DAYS_TO_CHECK=7
```

3. **Run with Docker Compose**:
```bash
docker-compose up --build
```

Or run directly with Python:
```bash
pip install -r requirements.txt
python padel_checker.py
```

---

## 📊 Monitoring

### View recent logs:
```bash
gcloud run services logs read padel-checker --region europe-west1 --limit 50
```

### Trigger a manual check:
```bash
gcloud scheduler jobs run padel-checker-job --location europe-west1
```

### Check scheduler status:
```bash
gcloud scheduler jobs describe padel-checker-job --location europe-west1
```

---

## ⚙️ Customization

### Change check frequency:
Edit the cron schedule in `deploy.sh`:
- Every 5 minutes: `*/5 * * * *`
- Every 10 minutes: `*/10 * * * *`
- Every hour: `0 * * * *`

### Change time range:
Edit `padel_checker.py` and modify:
```python
target_start = datetime.strptime('18:00:00', '%H:%M:%S').time()
target_end = datetime.strptime('21:00:00', '%H:%M:%S').time()
```

### Change location:
Edit `padel_checker.py` and modify:
```python
LOCATION_ID = 224  # Change to your location ID
```

---

## 💰 Cost

Running this on GCP costs approximately **$0.60-1.10/month**:
- Cloud Run: ~$0.50-1/month
- Cloud Scheduler: $0.10/month

---

## 🛑 Stopping the Service

To stop receiving notifications without deleting everything:
```bash
gcloud scheduler jobs pause padel-checker-job --location europe-west1
```

To resume:
```bash
gcloud scheduler jobs resume padel-checker-job --location europe-west1
```

To completely remove everything:
```bash
gcloud scheduler jobs delete padel-checker-job --location europe-west1
gcloud run services delete padel-checker --region europe-west1
gcloud iam service-accounts delete padel-scheduler@YOUR_PROJECT_ID.iam.gserviceaccount.com
```

---

## ❓ Troubleshooting

**Not receiving notifications?**
1. Check if your bot is started (send it `/start`)
2. Verify your chat ID is correct
3. Check logs: `gcloud run services logs read padel-checker --region europe-west1`

**Scheduler not running?**
1. Check status: `gcloud scheduler jobs describe padel-checker-job --location europe-west1`
2. Manually trigger: `gcloud scheduler jobs run padel-checker-job --location europe-west1`

**Need help?**
Check the full README.md for detailed troubleshooting steps.
