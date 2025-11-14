# GCS State Storage Setup

This guide explains how to set up Google Cloud Storage for storing the padel checker state.

## Why GCS?

The script now tracks state changes to avoid sending duplicate Telegram notifications. It only sends messages when:
- New courts become available
- Previously available courts are no longer available
- Any other changes in availability

## Quick Setup

### 1. Create a GCS Bucket

```bash
# Set your project ID
export PROJECT_ID="your-gcp-project-id"

# Create a bucket (choose a globally unique name)
gsutil mb -p $PROJECT_ID -l us-central1 gs://padel-checker-state-${PROJECT_ID}
```

Or via Terraform (add to your `terraform/main.tf`):

```hcl
resource "google_storage_bucket" "state_bucket" {
  name          = "padel-checker-state-${var.project_id}"
  location      = "US"
  force_destroy = true

  uniform_bucket_level_access = true

  lifecycle_rule {
    action {
      type = "Delete"
    }
    condition {
      age = 30  # Delete old state files after 30 days
    }
  }
}

# Grant Cloud Run service account access to the bucket
resource "google_storage_bucket_iam_member" "state_bucket_access" {
  bucket = google_storage_bucket.state_bucket.name
  role   = "roles/storage.objectAdmin"
  member = "serviceAccount:${google_service_account.cloud_run_sa.email}"
}
```

### 2. Set Environment Variable

Add to your `.env` file:

```bash
GCS_BUCKET_NAME=padel-checker-state-your-project-id
GCS_STATE_FILE=padel_state.json  # Optional, defaults to this
```

Add to your Terraform Cloud Run configuration:

```hcl
resource "google_cloud_run_service" "padel_checker" {
  # ... existing config ...

  template {
    spec {
      containers {
        env {
          name  = "GCS_BUCKET_NAME"
          value = google_storage_bucket.state_bucket.name
        }
        # ... other env vars ...
      }
    }
  }
}
```

### 3. Grant Permissions

If running locally, authenticate:

```bash
gcloud auth application-default login
```

If running on Cloud Run, ensure the service account has `Storage Object Admin` role:

```bash
gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:your-service-account@$PROJECT_ID.iam.gserviceaccount.com" \
  --role="roles/storage.objectAdmin"
```

## How It Works

1. **First Run**: No state exists, so it sends notifications and saves the current state
2. **Subsequent Runs**: Compares current availability with stored state
   - If **identical**: No notification sent
   - If **different**: Sends notification and updates state
3. **State Storage**: A JSON file in GCS containing:
   - Hash of current availability
   - Timestamp of last update
   - List of dates with availability

## State File Format

```json
{
  "state_hash": "a1b2c3d4...",
  "last_updated": "2025-11-14T10:30:00",
  "dates_with_availability": [
    "2025-11-15",
    "2025-11-17"
  ]
}
```

## Costs

GCS costs for this use case are **negligible**:
- Storage: ~$0.023/GB/month (state file is < 1KB)
- Operations: ~$0.004 per 10,000 reads/writes
- **Expected cost: < $0.01/month**

## Troubleshooting

### "GCS_BUCKET_NAME not set" warning
- Add `GCS_BUCKET_NAME` to your environment variables
- The script will still work but won't track state

### "Failed to initialize GCS client"
- Ensure you're authenticated (`gcloud auth application-default login`)
- Check service account has proper permissions
- Verify `GOOGLE_APPLICATION_CREDENTIALS` is set if using a service account key

### State not updating
- Check Cloud Run logs: `gcloud run services logs read padel-checker-service`
- Verify bucket exists: `gsutil ls gs://your-bucket-name`
- Check IAM permissions

## Testing

Test the state management locally:

```bash
# First run - should send notification and save state
python padel_checker.py

# Immediate second run - should skip notification (no changes)
python padel_checker.py

# View the state file
gsutil cat gs://your-bucket-name/padel_state.json
```

## Disable State Tracking

If you want to receive notifications every time (old behavior), simply don't set `GCS_BUCKET_NAME`.

