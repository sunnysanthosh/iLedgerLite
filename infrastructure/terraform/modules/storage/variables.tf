variable "project_id" {
  type = string
}

variable "region" {
  type = string
}

variable "env" {
  type = string
}

variable "app_service_account" {
  type        = string
  description = "App service account email granted objectAdmin on the receipts bucket"
}
