# App service account — used by K8s pods via Workload Identity
resource "google_service_account" "app" {
  account_id   = "ledgerlite-${var.env}-app"
  display_name = "LedgerLite ${var.env} App"
  project      = var.project_id
}

# Connect to Cloud SQL from pods
resource "google_project_iam_member" "app_cloudsql_client" {
  project = var.project_id
  role    = "roles/cloudsql.client"
  member  = "serviceAccount:${google_service_account.app.email}"
}

# Write app logs to Cloud Logging
resource "google_project_iam_member" "app_log_writer" {
  project = var.project_id
  role    = "roles/logging.logWriter"
  member  = "serviceAccount:${google_service_account.app.email}"
}

# Write metrics to Cloud Monitoring
resource "google_project_iam_member" "app_metric_writer" {
  project = var.project_id
  role    = "roles/monitoring.metricWriter"
  member  = "serviceAccount:${google_service_account.app.email}"
}
