resource "google_container_cluster" "main" {
  name     = "ledgerlite-${var.env}"
  location = var.region
  project  = var.project_id

  # Defer to the managed node pool below
  remove_default_node_pool = true
  initial_node_count       = 1

  network    = var.network
  subnetwork = var.subnetwork

  ip_allocation_policy {
    cluster_secondary_range_name  = var.pods_range_name
    services_secondary_range_name = var.services_range_name
  }

  # Private nodes only for production (staging skips this to avoid Cloud NAT cost)
  dynamic "private_cluster_config" {
    for_each = var.enable_private_nodes ? [1] : []
    content {
      enable_private_nodes    = true
      enable_private_endpoint = false
      master_ipv4_cidr_block  = "172.16.0.0/28"
    }
  }

  workload_identity_config {
    workload_pool = "${var.project_id}.svc.id.goog"
  }

  release_channel {
    channel = "REGULAR"
  }

  deletion_protection = var.env == "production"
}

resource "google_container_node_pool" "nodes" {
  name       = "ledgerlite-${var.env}-nodes"
  cluster    = google_container_cluster.main.name
  location   = var.region
  project    = var.project_id
  node_count = var.node_count

  node_config {
    machine_type = var.machine_type
    # Preemptible (spot) nodes for staging — ~70% cheaper, acceptable interruptions
    preemptible  = var.preemptible
    disk_size_gb = 50
    disk_type    = "pd-standard"

    oauth_scopes = [
      "https://www.googleapis.com/auth/cloud-platform",
    ]

    workload_metadata_config {
      mode = "GKE_METADATA"
    }
  }

  management {
    auto_repair  = true
    auto_upgrade = true
  }
}
