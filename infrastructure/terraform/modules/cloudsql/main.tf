resource "google_sql_database_instance" "postgres" {
  name             = "ledgerlite-${var.env}-pg"
  database_version = "POSTGRES_16"
  region           = var.region
  project          = var.project_id

  deletion_protection = var.env == "production"

  settings {
    # staging: db-f1-micro (~$10/mo) | production: 2 vCPU, 7.5 GB RAM (~$100/mo)
    tier              = var.env == "production" ? "db-custom-2-7680" : "db-f1-micro"
    availability_type = var.env == "production" ? "REGIONAL" : "ZONAL"
    disk_type         = "PD_SSD"
    disk_size         = var.env == "production" ? 50 : 20
    disk_autoresize   = true

    ip_configuration {
      ipv4_enabled    = false
      private_network = var.network_id
      # staging: allow unencrypted connections on private VPC (no external exposure)
      # production: set ENCRYPTED_ONLY
      ssl_mode = var.env == "production" ? "ENCRYPTED_ONLY" : "ALLOW_UNENCRYPTED_AND_ENCRYPTED"
    }

    backup_configuration {
      enabled                        = true
      start_time                     = "03:00"
      point_in_time_recovery_enabled = var.env == "production"
      backup_retention_settings {
        retained_backups = var.env == "production" ? 30 : 7
      }
    }

    database_flags {
      name  = "max_connections"
      value = "100"
    }
  }
}

resource "google_sql_database" "ledgerlite" {
  name     = "ledgerlite"
  instance = google_sql_database_instance.postgres.name
  project  = var.project_id
}

resource "google_sql_user" "ledgerlite" {
  name     = "ledgerlite"
  instance = google_sql_database_instance.postgres.name
  password = var.db_password
  project  = var.project_id
}
