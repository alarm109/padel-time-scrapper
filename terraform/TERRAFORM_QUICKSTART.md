# Terraform Quick Start

Deploy everything to GCP in 5 minutes using Terraform! 🚀

## Prerequisites

```bash
# Install Terraform (if not installed)
# macOS
brew install terraform

# Linux
wget https://releases.hashicorp.com/terraform/1.6.0/terraform_1.6.0_linux_amd64.zip
unzip terraform_1.6.0_linux_amd64.zip
sudo mv terraform /usr/local/bin/

# Verify installation
terraform version
```

## Step-by-Step Deployment

### 1. Authenticate with GCP (2 minutes)

```bash
# Login to Google Cloud
gcloud auth login

# Set your project
gcloud config set project YOUR_PROJECT_ID

# Enable application-default credentials for Terraform
gcloud auth application-default login
```

### 2. Configure Terraform (1 minute)

```bash
# Navigate to terraform directory
cd terraform

# Copy example configuration
cp terraform.tfvars.example terraform.tfvars

# Edit with your actual values
nano terraform.tfvars
```

Edit these required values:
```hcl
project_id = "your-gcp-project-id"              # Your GCP project
telegram_bot_token = "123456:ABCdef..."          # From @BotFather
telegram_chat_id = "123456789"                   # From @userinfobot
```

### 3. Deploy (2 minutes)

```bash
# Initialize Terraform
terraform init

# Preview what will be created
terraform plan

# Deploy (type 'yes' when prompted)
terraform apply
```

### 4. Test It! (1 minute)

```bash
# Manually trigger to test
gcloud scheduler jobs run padel-checker-job --location=europe-west1

# View logs
gcloud run services logs read padel-checker --region=europe-west1 --limit=50
```

## What Gets Created?

- ✅ Cloud Run service (runs your script)
- ✅ Cloud Scheduler job (triggers every 5 minutes)
- ✅ Secret Manager secrets (stores credentials securely)
- ✅ Service accounts with proper IAM permissions
- ✅ Container image in Google Container Registry

## Common Commands

```bash
# View outputs
terraform output

# Update after changes
terraform apply

# Pause the scheduler
gcloud scheduler jobs pause padel-checker-job --location=europe-west1

# Resume the scheduler
gcloud scheduler jobs resume padel-checker-job --location=europe-west1

# Destroy everything
terraform destroy
```

## Customization

Edit `terraform.tfvars` and run `terraform apply`:

```hcl
# Check every 10 minutes instead of 5
schedule = "*/10 * * * *"

# Check 14 days ahead instead of 7
days_to_check = 14

# Use different region
region = "us-central1"

# Use environment variables instead of Secret Manager
use_secret_manager = false
```

## Troubleshooting

**"Error 403: Permission denied"**
```bash
# Make sure you're authenticated
gcloud auth application-default login
```

**"Terraform not found"**
```bash
# Install Terraform first (see Prerequisites)
```

**"Cannot find Dockerfile"**
```bash
# Make sure you're in the terraform directory
cd terraform
ls -la Dockerfile padel_checker.py requirements.txt
```

## Cost

~$0.15-0.20/month total (mostly Cloud Scheduler)

## Why Terraform?

✅ **Infrastructure as Code**: Version control your infrastructure
✅ **Repeatable**: Deploy identical environments easily
✅ **Automated**: No manual clicking in GCP console
✅ **Safe**: Preview changes before applying
✅ **Reversible**: Destroy everything with one command

For detailed information, see [terraform/README.md](terraform/README.md)
