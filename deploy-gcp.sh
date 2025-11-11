#!/bin/bash

# Padel Court Checker - GCP Deployment Script
# This script automates the deployment to Google Cloud Platform

set -e

echo "🎾 Padel Court Checker - GCP Deployment Script"
echo "=============================================="

# Check if required variables are set
if [ -z "$PROJECT_ID" ]; then
    echo "❌ Error: PROJECT_ID environment variable not set"
    echo "Run: export PROJECT_ID='your-project-id'"
    exit 1
fi

if [ -z "$TELEGRAM_BOT_TOKEN" ]; then
    echo "❌ Error: TELEGRAM_BOT_TOKEN environment variable not set"
    echo "Run: export TELEGRAM_BOT_TOKEN='your-token'"
    exit 1
fi

if [ -z "$TELEGRAM_CHAT_ID" ]; then
    echo "❌ Error: TELEGRAM_CHAT_ID environment variable not set"
    echo "Run: export TELEGRAM_CHAT_ID='your-chat-id'"
    exit 1
fi

# Set default values
REGION=${REGION:-"europe-west1"}
LOCATION_ID=${LOCATION_ID:-"224"}
DAYS_TO_CHECK=${DAYS_TO_CHECK:-"7"}

echo ""
echo "Configuration:"
echo "  Project ID: $PROJECT_ID"
echo "  Region: $REGION"
echo "  Location ID: $LOCATION_ID"
echo "  Days to Check: $DAYS_TO_CHECK"
echo ""

# Set project
echo "📋 Setting GCP project..."
gcloud config set project $PROJECT_ID

# Enable required APIs
echo "🔧 Enabling required GCP APIs..."
gcloud services enable run.googleapis.com
gcloud services enable cloudscheduler.googleapis.com
gcloud services enable cloudbuild.googleapis.com

# Build container
echo "🏗️  Building container image..."
gcloud builds submit --tag gcr.io/$PROJECT_ID/padel-checker

# Deploy to Cloud Run
echo "🚀 Deploying to Cloud Run..."
gcloud run deploy padel-checker \
  --image gcr.io/$PROJECT_ID/padel-checker \
  --platform managed \
  --region $REGION \
  --no-allow-unauthenticated \
  --set-env-vars TELEGRAM_BOT_TOKEN="$TELEGRAM_BOT_TOKEN" \
  --set-env-vars TELEGRAM_CHAT_ID="$TELEGRAM_CHAT_ID" \
  --set-env-vars LOCATION_ID="$LOCATION_ID" \
  --set-env-vars DAYS_TO_CHECK="$DAYS_TO_CHECK" \
  --memory 256Mi \
  --cpu 1 \
  --timeout 300 \
  --max-instances 1

# Get Cloud Run service URL
SERVICE_URL=$(gcloud run services describe padel-checker \
  --platform managed \
  --region $REGION \
  --format 'value(status.url)')

echo "✅ Cloud Run service deployed: $SERVICE_URL"

# Create service account if it doesn't exist
echo "👤 Creating service account..."
gcloud iam service-accounts create padel-checker-scheduler \
  --display-name "Padel Checker Scheduler" 2>/dev/null || echo "Service account already exists"

# Grant permissions
echo "🔐 Granting permissions..."
gcloud run services add-iam-policy-binding padel-checker \
  --region=$REGION \
  --member=serviceAccount:padel-checker-scheduler@$PROJECT_ID.iam.gserviceaccount.com \
  --role=roles/run.invoker

# Delete existing scheduler job if it exists
echo "🗑️  Removing existing scheduler job (if any)..."
gcloud scheduler jobs delete padel-checker-job --location=$REGION --quiet 2>/dev/null || true

# Create scheduler job (runs every 5 minutes)
echo "⏰ Creating Cloud Scheduler job (runs every 5 minutes)..."
gcloud scheduler jobs create http padel-checker-job \
  --location=$REGION \
  --schedule="*/5 * * * *" \
  --uri="$SERVICE_URL" \
  --http-method=POST \
  --oidc-service-account-email=padel-checker-scheduler@$PROJECT_ID.iam.gserviceaccount.com \
  --oidc-token-audience="$SERVICE_URL"

echo ""
echo "✅ Deployment complete!"
echo ""
echo "📊 Next steps:"
echo "  1. Test the scheduler: gcloud scheduler jobs run padel-checker-job --location=$REGION"
echo "  2. View logs: gcloud run services logs read padel-checker --region=$REGION --limit 50"
echo "  3. List jobs: gcloud scheduler jobs list --location=$REGION"
echo ""
echo "💰 Estimated cost: ~\$0.10-0.15/month"
echo ""
