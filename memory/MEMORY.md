# LedgerLite — Session Memory

## Status: Sprint 6C COMPLETE. Next action: deploy staging.
Full details → `memory/full-context.md`

## GCP
- Project ID: `project-6737f3c2-e011-49b7-ae4`
- Region: `us-central1`
- State bucket (create once): `gs://project-6737f3c2-e011-49b7-ae4-tf-state`

## Immediate Next Steps (in order)
```bash
# 1. Prereqs
brew install terraform kubectl google-cloud-sdk
gcloud auth application-default login

# 2. State bucket (once)
gcloud storage buckets create gs://project-6737f3c2-e011-49b7-ae4-tf-state \
  --project=project-6737f3c2-e011-49b7-ae4 --location=us-central1

# 3. Terraform
cd infrastructure/terraform
terraform init
export TF_VAR_db_password="strong-password-here"
terraform apply -var-file=envs/staging.tfvars

# 4. Fill in Cloud SQL IP
# Edit infrastructure/kubernetes/overlays/staging/kustomization.yaml
# Replace CLOUD_SQL_PRIVATE_IP → terraform output cloudsql_private_ip
# Replace DATABASE_PASSWORD → same as TF_VAR_db_password
# Replace JWT_SECRET → a real secret

# 5. Connect kubectl
gcloud container clusters get-credentials ledgerlite-staging \
  --region us-central1 --project project-6737f3c2-e011-49b7-ae4

# 6. GHCR pull secret (if packages are private)
kubectl create namespace ledgerlite-staging
kubectl create secret docker-registry ghcr-pull-secret \
  --docker-server=ghcr.io --docker-username=sunnysans \
  --docker-password=<GITHUB_PAT> -n ledgerlite-staging

# 7. Deploy
kubectl apply -k infrastructure/kubernetes/overlays/staging

# 8. Watch migrations job
kubectl logs -l app.kubernetes.io/name=ledgerlite-migrations -n ledgerlite-staging -f

# 9. Verify
kubectl get pods -n ledgerlite-staging
kubectl get ingress -n ledgerlite-staging
```

## Staging Cost: ~$44/month
Cloud SQL $10 + GKE $10-15 + Load Balancer $18 + GCS $1

## User Preferences
- GCP not AWS. Concise communication. Staging-first, minimize costs.
- See `memory/full-context.md` for complete architecture, all files, all decisions.
