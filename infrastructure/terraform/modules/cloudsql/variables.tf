variable "project_id" {
  type = string
}

variable "region" {
  type = string
}

variable "env" {
  type = string
}

variable "network_id" {
  type        = string
  description = "VPC network ID for private IP connectivity"
}

variable "db_password" {
  type      = string
  sensitive = true
}
