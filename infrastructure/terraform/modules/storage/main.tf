resource "google_storage_bucket" "receipts" {
  # Project ID suffix ensures global uniqueness
  name                        = "ledgerlite-${var.env}-receipts-${var.project_id}"
  location                    = var.region
  project                     = var.project_id
  force_destroy               = var.env != "production"
  uniform_bucket_level_access = true

  versioning {
    enabled = var.env == "production"
  }

  # Move old receipts to cheaper storage after 1 year
  lifecycle_rule {
    condition {
      age = 365
    }
    action {
      type          = "SetStorageClass"
      storage_class = "NEARLINE"
    }
  }

  cors {
    origin          = ["*"]
    method          = ["GET", "HEAD", "PUT", "POST"]
    response_header = ["Content-Type", "Authorization"]
    max_age_seconds = 3600
  }
}

# Grant the app service account full object access on this bucket
resource "google_storage_bucket_iam_member" "app_object_admin" {
  bucket = google_storage_bucket.receipts.name
  role   = "roles/storage.objectAdmin"
  member = "serviceAccount:${var.app_service_account}"
}
