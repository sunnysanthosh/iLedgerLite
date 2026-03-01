terraform {
  backend "gcs" {
    # Create this bucket once before running terraform init:
    # gcloud storage buckets create gs://project-6737f3c2-e011-49b7-ae4-tf-state \
    #   --project=project-6737f3c2-e011-49b7-ae4 \
    #   --location=us-central1
    bucket = "project-6737f3c2-e011-49b7-ae4-tf-state"
    prefix = "terraform/state"
  }
}
