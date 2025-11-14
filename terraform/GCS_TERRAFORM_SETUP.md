# Terraform GCS Setup - Quick Guide

## What Was Added

The Terraform configuration now includes:

1. **GCS Bucket** (`google_storage_bucket.state_bucket`)
   - Name: `padel-checker-state-{project_id}`
   - Location: US
   - Versioning enabled (keeps history of state changes)
   - Auto-cleanup: Deletes files older than 30 days

2. **Storage API** enablement

3. **IAM Permissions** for Cloud Run service account
   - Role: `roles/storage.objectAdmin`
   - Allows reading and writing state files

4. **Environment Variables** in Cloud Run job
   - `GCS_BUCKET_NAME`: Automatically set to bucket name
   - `GCS_STATE_FILE`: Set to `padel_state.json`

5. **Outputs**
   - `state_bucket_name`: Shows the bucket name
   - `view_state_command`: Command to view current state

## How to Apply

### 1. Review Changes

```bash
cd terraform
terraform plan
```

You should see:
- `google_storage_bucket.state_bucket` will be created
- `google_storage_bucket_iam_member.state_bucket_access` will be created
- `google_project_service.storage` will be created
- `google_cloud_run_v2_job.padel_checker` will be updated (new env vars)

### 2. Apply Changes

```bash
terraform apply
```

Type `yes` when prompted.

### 3. Verify

After applying, you'll see outputs including:

```
state_bucket_name = "padel-checker-state-your-project-id"
view_state_command = "gsutil cat gs://padel-checker-state-your-project-id/padel_state.json"
```

### 4. Test

Manually trigger the job to create the initial state:

```bash
# Get the trigger command from outputs
terraform output trigger_job_command

# Or run directly
gcloud scheduler jobs run padel-checker-job --location=europe-west1
```

### 5. View State

After the first run, check the state file:

```bash
gsutil cat gs://padel-checker-state-your-project-id/padel_state.json
```

You should see something like:

```json
{
  "state_hash": "a1b2c3d4e5f6...",
  "last_updated": "2025-11-14T10:30:00.123456",
  "dates_with_availability": [
    "2025-11-15",
    "2025-11-17"
  ]
}
```

## What Happens Next

1. **First run**: Creates state file, sends Telegram notification
2. **Subsequent runs (no changes)**: Checks state, skips notification
3. **Subsequent runs (changes)**: Updates state, sends notification

## Resources Created

| Resource | Type | Purpose |
|----------|------|---------|
| `padel-checker-state-{project_id}` | GCS Bucket | Stores state JSON |
| IAM binding | Bucket permission | Allows Cloud Run to read/write |

## Cost

- **Storage**: ~$0.023/GB/month (state file < 1KB = negligible)
- **Operations**: ~$0.004 per 10,000 reads/writes
- **Total expected**: < $0.01/month

## Troubleshooting

### State file not being created

Check Cloud Run logs:
```bash
gcloud logging read "resource.type=cloud_run_job AND resource.labels.job_name=padel-checker" --limit 50 --format json
```

### Permission denied errors

Verify IAM binding:
```bash
gsutil iam get gs://padel-checker-state-your-project-id
```

### Delete and recreate bucket

If you need to start fresh:
```bash
gsutil rm -r gs://padel-checker-state-your-project-id
terraform apply
```

## Optional: Change Bucket Location

Edit `terraform/main.tf`:

```hcl
resource "google_storage_bucket" "state_bucket" {
  name     = "padel-checker-state-${var.project_id}"
  location = "EU"  # Change from "US" to "EU" or specific region
  # ...
}
```

Then run `terraform apply`.

## Optional: Disable Versioning

If you don't need version history, remove the versioning block from `main.tf`:

```hcl
# Remove this:
versioning {
  enabled = true
}
```

## Optional: Adjust Cleanup Period

Change the lifecycle rule age in `main.tf`:

```hcl
lifecycle_rule {
  action {
    type = "Delete"
  }
  condition {
    age = 90  # Change from 30 to 90 days
  }
}
```

