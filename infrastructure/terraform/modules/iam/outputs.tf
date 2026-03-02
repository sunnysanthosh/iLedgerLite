output "app_service_account_email" {
  description = "Annotate K8s ServiceAccounts with iam.gke.io/gcp-service-account=<this value>"
  value       = google_service_account.app.email
}

output "app_service_account_id" {
  description = "Full resource ID of the app service account (for IAM bindings)"
  value       = google_service_account.app.name
}

output "ci_service_account_email" {
  description = "CI SA email for staging start/stop workflows (null in production)"
  value       = var.env == "staging" ? google_service_account.ci[0].email : null
}
