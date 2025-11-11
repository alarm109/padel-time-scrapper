# Terraform Deployment for Padel Court Checker

This directory contains Terraform configuration to deploy the Padel Court Checker to Google Cloud Platform automatically.

## What It Deploys

- ☁️ **Cloud Run**: Serverless container for the checker script
- ⏰ **Cloud Scheduler**: Triggers the script every 5 minutes
- 🔐 **Secret Manager**: Securely stores Telegram credentials (optional)
- 👤 **Service Accounts**: IAM roles and permissions
- 🔧 **APIs**: Enables all required GCP services

## Prerequisites

1. **Google Cloud SDK**: [Install gcloud](https://cloud.google.com/sdk/docs/install)
2. **Terraform**: [Install Terraform](https://developer.hashicorp.com/terraform/downloads) (>= 1.0)
3. **GCP Project**: With billing enabled
4. **Telegram Bot**: Bot token and chat ID (see main README.md)

## Quick Start (5 minutes)

### Step 1: Authenticate with GCP

```bash
# Login to GCP
gcloud auth login

# Set your project
gcloud config set project YOUR_PROJECT_ID

# Enable application default credentials for Terraform
gcloud auth application-default login
```

### Step 2: Configure Terraform Variables

```bash
# Copy the example file
cp terraform.tfvars.example terraform.tfvars

# Edit with your values
nano terraform.tfvars
```

**Important:** Replace the placeholder values with your actual credentials:
```hcl
project_id = "your-actual-project-id"
telegram_bot_token = "your-actual-bot-token"
telegram_chat_id = "your-actual-chat-id"
```

### Step 3: Copy Required Files

Make sure these files are in the terraform directory:
```bash
# Copy from parent directory
cp ../padel_checker.py .
cp ../requirements.txt .
cp ../Dockerfile .
```

Or create symlinks:
```bash
ln -s ../padel_checker.py padel_checker.py
ln -s ../requirements.txt requirements.txt
ln -s ../Dockerfile Dockerfile
```

### Step 4: Deploy!

```bash
# Initialize Terraform
terraform init

# Preview changes
terraform plan

# Deploy (type 'yes' when prompted)
terraform apply
```

That's it! Your padel checker is now running on GCP! 🎉

## What Happens During Deployment

1. **Enables GCP APIs** (Cloud Run, Scheduler, Build, Secret Manager)
2. **Creates secrets** in Secret Manager for your Telegram credentials
3. **Builds container** using Google Cloud Build
4. **Deploys to Cloud Run** with your configuration
5. **Creates scheduler** to run every 5 minutes
6. **Sets up IAM** permissions for everything to work

## Post-Deployment

After `terraform apply` completes, you'll see useful outputs:

```bash
Outputs:

cloud_run_service_url = "https://padel-checker-xxx-ew.a.run.app"
trigger_job_command = "gcloud scheduler jobs run padel-checker-job --location=europe-west1"
view_logs_command = "gcloud run services logs read padel-checker --region=europe-west1 --limit=50"
```

### Test the Deployment

```bash
# Manually trigger the job
terraform output -raw trigger_job_command | bash

# View logs
terraform output -raw view_logs_command | bash
```

## Configuration Options

### Change Schedule

Edit `terraform.tfvars`:
```hcl
schedule = "*/10 * * * *"  # Every 10 minutes
schedule = "0 * * * *"     # Every hour
schedule = "0 9 * * *"     # Daily at 9 AM
```

Then apply:
```bash
terraform apply
```

### Change Region

Edit `terraform.tfvars`:
```hcl
region = "us-central1"  # or any other GCP region
```

### Disable Secret Manager (Use Environment Variables)

Edit `terraform.tfvars`:
```hcl
use_secret_manager = false
```

**Note:** Less secure but simpler. Credentials will be in Cloud Run environment variables.

### Check More Days

Edit `terraform.tfvars`:
```hcl
days_to_check = 14  # Check 2 weeks ahead
```

## Managing the Deployment

### View Logs

```bash
# Using Terraform output
terraform output -raw view_logs_command | bash

# Or directly
gcloud run services logs read padel-checker --region=europe-west1 --limit=50
```

### Pause the Scheduler

```bash
# Using Terraform output
terraform output -raw pause_job_command | bash

# Or directly
gcloud scheduler jobs pause padel-checker-job --location=europe-west1
```

### Resume the Scheduler

```bash
# Using Terraform output
terraform output -raw resume_job_command | bash

# Or directly
gcloud scheduler jobs resume padel-checker-job --location=europe-west1
```

### Update the Code

After modifying `padel_checker.py`:

```bash
# Rebuild and redeploy
terraform apply -replace=null_resource.build_image
```

### Update Configuration Only

After changing `terraform.tfvars`:

```bash
terraform apply
```

## Destroy Everything

To remove all resources and stop charges:

```bash
terraform destroy
```

Type `yes` when prompted. This will delete:
- Cloud Run service
- Cloud Scheduler job
- Service accounts
- Secrets (if using Secret Manager)
- Container images (manual cleanup needed)

**Note:** Container images in GCR need manual deletion:
```bash
gcloud container images delete gcr.io/YOUR_PROJECT_ID/padel-checker
```

## Troubleshooting

### "Error 403: Cloud Build has not been used"

Enable the API manually:
```bash
gcloud services enable cloudbuild.googleapis.com
```

### "Error 403: Permission denied"

Make sure you have the necessary IAM roles:
```bash
gcloud projects add-iam-policy-binding YOUR_PROJECT_ID \
  --member="user:your-email@example.com" \
  --role="roles/owner"
```

### "Terraform can't find Docker files"

Make sure you copied or symlinked the required files:
```bash
ls -la padel_checker.py requirements.txt Dockerfile
```

### "Secret Manager API not enabled"

If you see this error and `use_secret_manager = true`:
```bash
gcloud services enable secretmanager.googleapis.com
terraform apply
```

### Container Build Fails

Check Cloud Build logs:
```bash
gcloud builds list --limit=5
gcloud builds log <BUILD_ID>
```

## Cost Estimation

With Terraform deployment:
- **Cloud Run**: ~$0.01-0.05/month (free tier)
- **Cloud Scheduler**: ~$0.10/month (3 free jobs)
- **Secret Manager**: ~$0.06/month (6 secret versions)
- **Cloud Build**: Free (first 120 builds/day)

**Total**: ~$0.15-0.20/month

## Terraform State

Terraform creates a `terraform.tfstate` file that tracks your infrastructure.

**Important:**
- 🔐 Never commit `terraform.tfstate` to git (contains sensitive data)
- 📦 For production, use [remote state](https://developer.hashicorp.com/terraform/language/state/remote)
- 💾 Back up your state file

### Remote State (Recommended for Production)

Add to `main.tf`:
```hcl
terraform {
  backend "gcs" {
    bucket = "your-terraform-state-bucket"
    prefix = "padel-checker"
  }
}
```

## Directory Structure

```
terraform/
├── main.tf                    # Main resources
├── variables.tf               # Input variables
├── outputs.tf                 # Output values
├── terraform.tfvars.example   # Example configuration
├── terraform.tfvars           # Your actual config (gitignored)
├── .gitignore                 # Ignore sensitive files
├── README.md                  # This file
├── padel_checker.py          # Symlink or copy from parent
├── requirements.txt          # Symlink or copy from parent
└── Dockerfile                # Symlink or copy from parent
```

## Advanced: Multi-Environment Setup

For dev/staging/prod environments:

```bash
# Create workspaces
terraform workspace new dev
terraform workspace new prod

# Switch workspace
terraform workspace select dev

# Use workspace-specific vars
terraform apply -var-file="dev.tfvars"
```

## Support

If you encounter issues:
1. Check the [main README](../README.md) for general setup
2. Verify GCP permissions and enabled APIs
3. Check Terraform version: `terraform version`
4. View detailed errors: `terraform apply -debug`

## Useful Commands

```bash
# Show current state
terraform show

# List all resources
terraform state list

# Show specific resource
terraform state show google_cloud_run_v2_service.padel_checker

# Format code
terraform fmt

# Validate configuration
terraform validate

# Show outputs
terraform output

# Refresh state
terraform refresh
```

## Next Steps

After successful deployment:
1. ✅ Test manually: `terraform output -raw trigger_job_command | bash`
2. ✅ Check logs: `terraform output -raw view_logs_command | bash`
3. ✅ Wait for Telegram message when slots are found
4. ✅ Adjust schedule if needed in `terraform.tfvars`

Enjoy your automated padel court checker! 🎾
