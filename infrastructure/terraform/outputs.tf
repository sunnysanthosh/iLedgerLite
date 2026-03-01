output "gke_cluster_name" {
  description = "GKE cluster name"
  value       = module.gke.cluster_name
}

output "gke_cluster_endpoint" {
  description = "GKE cluster API endpoint"
  value       = module.gke.cluster_endpoint
  sensitive   = true
}

output "cloudsql_connection_name" {
  description = "Cloud SQL connection name (for Cloud SQL Auth Proxy)"
  value       = module.cloudsql.connection_name
}

output "cloudsql_private_ip" {
  description = "Cloud SQL private IP address"
  value       = module.cloudsql.private_ip
}

output "redis_host" {
  description = "Memorystore Redis host (production only — staging uses in-cluster Redis)"
  value       = module.memorystore.host
}

output "redis_port" {
  description = "Memorystore Redis port"
  value       = module.memorystore.port
}

output "receipts_bucket_name" {
  description = "GCS bucket name for receipt uploads"
  value       = module.storage.bucket_name
}

output "app_service_account_email" {
  description = "App service account email — annotate K8s ServiceAccounts with this for Workload Identity"
  value       = module.iam.app_service_account_email
}

output "database_url" {
  description = "PostgreSQL async connection URL for app services"
  value       = "postgresql+asyncpg://ledgerlite:${var.db_password}@${module.cloudsql.private_ip}:5432/ledgerlite"
  sensitive   = true
}

output "redis_url" {
  description = "Redis URL — production: Memorystore, staging: in-cluster redis service"
  value       = var.environment == "production" ? "redis://${module.memorystore.host}:${module.memorystore.port}" : "redis://redis:6379"
}

output "connect_to_cluster" {
  description = "Command to configure kubectl"
  value       = "gcloud container clusters get-credentials ${module.gke.cluster_name} --region ${var.region} --project ${var.project_id}"
}
