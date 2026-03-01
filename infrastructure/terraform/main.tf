terraform {
  required_version = ">= 1.6"
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
  }
}

provider "google" {
  project = var.project_id
  region  = var.region
}

# ---------------------------------------------------------------------------
# Enable required GCP APIs
# ---------------------------------------------------------------------------
locals {
  required_apis = [
    "container.googleapis.com",
    "sqladmin.googleapis.com",
    "redis.googleapis.com",
    "storage.googleapis.com",
    "servicenetworking.googleapis.com",
    "iam.googleapis.com",
    "cloudresourcemanager.googleapis.com",
  ]
}

resource "google_project_service" "apis" {
  for_each           = toset(local.required_apis)
  project            = var.project_id
  service            = each.value
  disable_on_destroy = false
}

# ---------------------------------------------------------------------------
# Modules
# ---------------------------------------------------------------------------
module "iam" {
  source     = "./modules/iam"
  project_id = var.project_id
  env        = var.environment
  depends_on = [google_project_service.apis]
}

module "vpc" {
  source     = "./modules/vpc"
  project_id = var.project_id
  region     = var.region
  env        = var.environment
  depends_on = [google_project_service.apis]
}

module "gke" {
  source              = "./modules/gke"
  project_id          = var.project_id
  region              = var.region
  env                 = var.environment
  network             = module.vpc.network_name
  subnetwork          = module.vpc.subnetwork_name
  pods_range_name     = module.vpc.pods_range_name
  services_range_name = module.vpc.services_range_name
  # staging: 1 preemptible e2-medium, public nodes (no NAT cost)
  # production: 2 standard e2-standard-2, private nodes
  enable_private_nodes = var.environment == "production"
  node_count           = var.environment == "production" ? 2 : 1
  machine_type         = var.environment == "production" ? "e2-standard-2" : "e2-medium"
  preemptible          = var.environment != "production"
  depends_on           = [module.vpc, module.iam]
}

module "cloudsql" {
  source      = "./modules/cloudsql"
  project_id  = var.project_id
  region      = var.region
  env         = var.environment
  network_id  = module.vpc.network_id
  db_password = var.db_password
  depends_on  = [module.vpc]
}

module "memorystore" {
  source     = "./modules/memorystore"
  project_id = var.project_id
  region     = var.region
  env        = var.environment
  network_id = module.vpc.network_id
  depends_on = [module.vpc]
}

module "storage" {
  source              = "./modules/storage"
  project_id          = var.project_id
  region              = var.region
  env                 = var.environment
  app_service_account = module.iam.app_service_account_email
  depends_on          = [module.iam]
}
