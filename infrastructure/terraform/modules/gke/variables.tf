variable "project_id" {
  type = string
}

variable "region" {
  type = string
}

variable "env" {
  type = string
}

variable "network" {
  type        = string
  description = "VPC network name"
}

variable "subnetwork" {
  type        = string
  description = "Subnetwork name for GKE nodes"
}

variable "pods_range_name" {
  type        = string
  description = "Secondary range name for GKE pods"
}

variable "services_range_name" {
  type        = string
  description = "Secondary range name for GKE services"
}

variable "enable_private_nodes" {
  type        = bool
  description = "Enable private nodes (requires Cloud NAT). True for production, false for staging."
}

variable "node_count" {
  type        = number
  description = "Number of nodes in the node pool"
}

variable "machine_type" {
  type        = string
  description = "GCE machine type for nodes"
}

variable "preemptible" {
  type        = bool
  description = "Use preemptible (spot) nodes — cheaper but can be interrupted"
}
