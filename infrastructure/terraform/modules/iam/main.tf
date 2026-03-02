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

# ---------------------------------------------------------------------------
# CI service account — used by GitHub Actions staging start/stop workflows
# Scoped to staging only; not created for production.
# ---------------------------------------------------------------------------
resource "google_service_account" "ci" {
  count        = var.env == "staging" ? 1 : 0
  account_id   = "ledgerlite-ci"
  display_name = "LedgerLite CI (staging start/stop)"
  project      = var.project_id
}

# Resize GKE node pools (scale to 0 / restore) — requires container.clusters.update
resource "google_project_iam_member" "ci_container_admin" {
  count   = var.env == "staging" ? 1 : 0
  project = var.project_id
  role    = "roles/container.admin"
  member  = "serviceAccount:${google_service_account.ci[0].email}"
}

# Patch Cloud SQL activation policy (ALWAYS / NEVER) — requires cloudsql.instances.update
resource "google_project_iam_member" "ci_cloudsql_admin" {
  count   = var.env == "staging" ? 1 : 0
  project = var.project_id
  role    = "roles/cloudsql.admin"
  member  = "serviceAccount:${google_service_account.ci[0].email}"
}
