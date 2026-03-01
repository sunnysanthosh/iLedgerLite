# Skipped for staging — staging uses the in-cluster Redis pod (already in K8s base manifests)
# This saves ~$35/month. Production uses managed Memorystore for reliability.
resource "google_redis_instance" "redis" {
  count          = var.env == "production" ? 1 : 0
  name           = "ledgerlite-${var.env}-redis"
  display_name   = "LedgerLite ${var.env} Redis"
  project        = var.project_id
  region         = var.region
  redis_version  = "REDIS_7_0"
  memory_size_gb = 2

  # STANDARD_HA = replicated with automatic failover (production only)
  tier = "STANDARD_HA"

  authorized_network = var.network_id

  auth_enabled = true
}
