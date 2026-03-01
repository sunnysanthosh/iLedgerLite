output "app_service_account_email" {
  description = "Annotate K8s ServiceAccounts with iam.gke.io/gcp-service-account=<this value>"
  value       = google_service_account.app.email
}
