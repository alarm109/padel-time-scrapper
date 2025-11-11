# 🎾 Padel Court Checker - START HERE

Welcome! This guide will help you deploy an automated padel court availability checker.

## What Does This Do?

🔍 Automatically checks for available padel court slots
⏰ Finds 3 consecutive 30-minute slots (18:00-21:00)
📱 Sends you Telegram messages when slots are found
🤖 Runs every 5 minutes automatically on Google Cloud

## 🚀 Choose Your Path

### Path 1: Quick Start (5 minutes)
**Best for:** Getting started quickly

1. Read [QUICKSTART.md](QUICKSTART.md)
2. Get Telegram credentials (2 min)
3. Deploy with bash script (3 min)
4. Done! ✅

### Path 2: Production Deployment (10 minutes)
**Best for:** Serious/long-term use ⭐ RECOMMENDED

1. Read [TERRAFORM_QUICKSTART.md](TERRAFORM_QUICKSTART.md)
2. Install Terraform (2 min)
3. Configure and deploy (5 min)
4. Professional setup! ✅

### Path 3: Local Testing (2 minutes)
**Best for:** Testing before cloud deployment

1. Read [LOCAL_TESTING.md](LOCAL_TESTING.md)
2. Create .env file (1 min)
3. Run locally (1 min)
4. Test complete! ✅

## 📚 Documentation Overview

### Getting Started
- **[QUICKSTART.md](QUICKSTART.md)** - Fast 5-minute setup with bash
- **[TERRAFORM_QUICKSTART.md](TERRAFORM_QUICKSTART.md)** - Production setup with Terraform
- **[LOCAL_TESTING.md](LOCAL_TESTING.md)** - Test on your computer first
- **[DEPLOYMENT_COMPARISON.md](DEPLOYMENT_COMPARISON.md)** - Which method to choose?

### Reference
- **[README.md](README.md)** - Complete documentation
- **[COMMANDS.md](COMMANDS.md)** - All commands in one place
- **[PROJECT_STRUCTURE.md](PROJECT_STRUCTURE.md)** - File overview

### Terraform (Advanced)
- **[terraform/README.md](terraform/README.md)** - Detailed Terraform guide
- **[terraform/](terraform/)** - All Terraform files

## 🎯 Recommended Quick Start

**First time? Do this:**

```bash
# 1. Get Telegram bot token from @BotFather
# 2. Get your chat ID from @userinfobot
# 3. Set environment variables
export PROJECT_ID="your-gcp-project-id"
export TELEGRAM_BOT_TOKEN="your-bot-token"
export TELEGRAM_CHAT_ID="your-chat-id"

# 4. Deploy!
./deploy-gcp.sh
```

**Want production-grade? Use Terraform:**

```bash
cd terraform
cp terraform.tfvars.example terraform.tfvars
# Edit terraform.tfvars with your values
terraform init
terraform apply
```

**Just testing? Run locally:**

```bash
# Create .env file
cat > .env << EOF
TELEGRAM_BOT_TOKEN=your_token
TELEGRAM_CHAT_ID=your_chat_id
EOF

# Run
pip install -r requirements.txt
python padel_checker.py
```

## 📋 Prerequisites

### Required
- ✅ Google Cloud Platform account (with billing)
- ✅ Telegram bot (get from @BotFather)
- ✅ Telegram chat ID (get from @userinfobot)

### Optional (depending on method)
- 🔧 Google Cloud SDK (for bash deployment)
- 🔧 Terraform (for Terraform deployment)
- 🐳 Docker (for local testing with containers)

## 💡 Which Deployment Method?

| Method | Best For | Time | Difficulty |
|--------|----------|------|-----------|
| **Bash Script** | Quick personal projects | 5 min | ⭐ Easy |
| **Terraform** | Production/team use | 10 min | ⭐⭐ Moderate |
| **Local/Docker** | Testing only | 2 min | ⭐ Very Easy |

See [DEPLOYMENT_COMPARISON.md](DEPLOYMENT_COMPARISON.md) for detailed comparison.

## 🎓 New to GCP?

Don't worry! Here's what you need:

1. **Create GCP Account**: [cloud.google.com](https://cloud.google.com)
2. **Create Project**: In GCP Console → New Project
3. **Enable Billing**: Add payment method (you get $300 free credits!)
4. **Install gcloud**: [Install guide](https://cloud.google.com/sdk/docs/install)

## 🎓 New to Telegram Bots?

Easy! Just:

1. **Open Telegram**
2. **Message @BotFather**
3. **Send:** `/newbot`
4. **Follow instructions**
5. **Save your bot token** (looks like: `123456:ABCdef...`)
6. **Message @userinfobot** to get your chat ID

## ⚙️ Configuration

All methods use these settings:

| Setting | Default | What it does |
|---------|---------|--------------|
| `LOCATION_ID` | 224 | Which court location |
| `DAYS_TO_CHECK` | 7 | How many days ahead to check |
| Schedule | Every 5 min | How often to check |
| Time range | 18:00-21:00 | What time slots to look for |
| Slot count | 3×30min | How many consecutive slots |

## 💰 Cost

**Very cheap!** ~$0.10-0.20/month

- Cloud Run: Free tier covers it
- Cloud Scheduler: $0.10/month
- Secret Manager: $0.06/month (if used)

## 🔍 After Deployment

### Check if it's working:

```bash
# View logs
gcloud run services logs read padel-checker --region=europe-west1 --limit=50

# Trigger manually
gcloud scheduler jobs run padel-checker-job --location=europe-west1
```

### Customize:

Edit these values and redeploy:
- Check every 10 minutes instead of 5
- Look for different time slots
- Check more days ahead
- Different court location

## 🆘 Need Help?

1. **Not working?** Check [README.md](README.md) troubleshooting section
2. **Commands?** See [COMMANDS.md](COMMANDS.md)
3. **Local testing issues?** Read [LOCAL_TESTING.md](LOCAL_TESTING.md)

## 📁 Files Included

### Core Files
- `padel_checker.py` - Main Python script
- `requirements.txt` - Python dependencies
- `Dockerfile` - Container definition
- `docker-compose.yml` - Local testing config
- `.env.example` - Configuration template

### Deployment Scripts
- `deploy-gcp.sh` - Bash deployment script
- `terraform/` - Terraform configuration (production)

### Documentation
- `START_HERE.md` - This file! 👋
- `README.md` - Complete guide
- `QUICKSTART.md` - 5-minute setup
- `TERRAFORM_QUICKSTART.md` - Terraform setup
- `LOCAL_TESTING.md` - Test locally
- `COMMANDS.md` - Command reference
- `DEPLOYMENT_COMPARISON.md` - Compare methods

## 🎯 Next Steps

1. **Choose a deployment method** (see comparison above)
2. **Follow the relevant quickstart guide**
3. **Deploy and test**
4. **Enjoy automated notifications!** 🎉

## 🤔 Still Deciding?

**If you want:**
- ✨ Fastest setup → Use **bash script** ([QUICKSTART.md](QUICKSTART.md))
- 🏆 Best practices → Use **Terraform** ([TERRAFORM_QUICKSTART.md](TERRAFORM_QUICKSTART.md))
- 🧪 Just testing → Run **locally** ([LOCAL_TESTING.md](LOCAL_TESTING.md))

**Not sure?** Start with local testing, then deploy with Terraform when ready!

---

**Ready?** Pick your path above and get started! 🚀

Questions? Check [README.md](README.md) for detailed documentation.
