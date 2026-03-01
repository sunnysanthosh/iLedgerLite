output "connection_name" {
  description = "Cloud SQL connection name — use with Cloud SQL Auth Proxy"
  value       = google_sql_database_instance.postgres.connection_name
}

output "private_ip" {
  description = "Private IP — use directly from GKE pods via VPC"
  value       = google_sql_database_instance.postgres.private_ip_address
}

output "instance_name" {
  value = google_sql_database_instance.postgres.name
}
