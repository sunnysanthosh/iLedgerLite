output "host" {
  value = length(google_redis_instance.redis) > 0 ? google_redis_instance.redis[0].host : ""
}

output "port" {
  value = length(google_redis_instance.redis) > 0 ? google_redis_instance.redis[0].port : 6379
}

output "auth_string" {
  description = "Redis AUTH token (production only) — inject as REDIS_PASSWORD env var in K8s secret"
  value       = length(google_redis_instance.redis) > 0 ? google_redis_instance.redis[0].auth_string : ""
  sensitive   = true
}
