output "network_name" {
  value = google_compute_network.vpc.name
}

output "network_id" {
  value = google_compute_network.vpc.id
}

output "subnetwork_name" {
  value = google_compute_subnetwork.gke.name
}

output "pods_range_name" {
  value = "gke-pods"
}

output "services_range_name" {
  value = "gke-services"
}
