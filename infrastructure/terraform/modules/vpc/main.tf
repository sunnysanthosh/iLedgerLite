resource "google_compute_network" "vpc" {
  name                    = "ledgerlite-${var.env}-vpc"
  auto_create_subnetworks = false
  project                 = var.project_id
}

# Subnet for GKE pods and services (with secondary IP ranges)
resource "google_compute_subnetwork" "gke" {
  name          = "ledgerlite-${var.env}-gke-subnet"
  ip_cidr_range = "10.0.0.0/20"
  region        = var.region
  network       = google_compute_network.vpc.id
  project       = var.project_id

  secondary_ip_range {
    range_name    = "gke-pods"
    ip_cidr_range = "10.16.0.0/14"
  }

  secondary_ip_range {
    range_name    = "gke-services"
    ip_cidr_range = "10.20.0.0/20"
  }

  private_ip_google_access = true
}

# Reserve a private IP range for Cloud SQL and Memorystore (VPC peering)
resource "google_compute_global_address" "private_service_range" {
  name          = "ledgerlite-${var.env}-private-range"
  purpose       = "VPC_PEERING"
  address_type  = "INTERNAL"
  prefix_length = 16
  network       = google_compute_network.vpc.id
  project       = var.project_id
}

resource "google_service_networking_connection" "private_vpc_connection" {
  network                 = google_compute_network.vpc.id
  service                 = "servicenetworking.googleapis.com"
  reserved_peering_ranges = [google_compute_global_address.private_service_range.name]
}

# Firewall: allow all traffic within the VPC (10.x.x.x)
resource "google_compute_firewall" "allow_internal" {
  name    = "ledgerlite-${var.env}-allow-internal"
  network = google_compute_network.vpc.name
  project = var.project_id

  allow {
    protocol = "tcp"
  }
  allow {
    protocol = "udp"
  }
  allow {
    protocol = "icmp"
  }

  source_ranges = ["10.0.0.0/8"]
}

# Cloud Router + NAT — required for private GKE nodes to reach the internet
# Skipped for staging (staging uses public nodes to avoid the ~$32/month NAT cost)
resource "google_compute_router" "nat_router" {
  count   = var.env == "production" ? 1 : 0
  name    = "ledgerlite-${var.env}-router"
  region  = var.region
  network = google_compute_network.vpc.id
  project = var.project_id
}

resource "google_compute_router_nat" "nat" {
  count                              = var.env == "production" ? 1 : 0
  name                               = "ledgerlite-${var.env}-nat"
  router                             = google_compute_router.nat_router[0].name
  region                             = var.region
  project                            = var.project_id
  nat_ip_allocate_option             = "AUTO_ONLY"
  source_subnetwork_ip_ranges_to_nat = "ALL_SUBNETWORKS_ALL_IP_RANGES"

  log_config {
    enable = false
    filter = "ERRORS_ONLY"
  }
}

# Firewall: allow GCP health check probes (required for GKE load balancers)
resource "google_compute_firewall" "allow_health_checks" {
  name    = "ledgerlite-${var.env}-allow-health-checks"
  network = google_compute_network.vpc.name
  project = var.project_id

  allow {
    protocol = "tcp"
  }

  source_ranges = ["130.211.0.0/22", "35.191.0.0/16"]
}
