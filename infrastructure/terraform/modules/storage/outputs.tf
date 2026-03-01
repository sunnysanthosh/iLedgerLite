output "bucket_name" {
  value = google_storage_bucket.receipts.name
}

output "bucket_url" {
  value = google_storage_bucket.receipts.url
}
