# GitHub Actions — Environments & Secrets Setup

This document explains the one-time setup required to make the [Deploy workflow](../../.github/workflows/deploy.yml) functional.

## 1. Create GitHub Environments

Go to: **GitHub → repo → Settings → Environments → New environment**

Create two environments: `staging` and `production`.

For `production`, add required reviewers (e.g., yourself) to require manual approval before every production deploy.

## 2. Add Secrets to Each Environment

Under each environment, click **Add secret** and add the following four secrets:

| Secret name | Value | Where to get it |
|---|---|---|
| `KUBECONFIG` | base64-encoded kubeconfig | See section 3 below |
| `DB_PASSWORD` | Cloud SQL ledgerlite user password | `eAhI8CmeZ20UFJL7KXI6wvzcP0tp` for staging |
| `JWT_SECRET` | HS256 JWT signing secret | `6f262023...` for staging — see apply-secrets.sh |
| `DATABASE_URL` | Full asyncpg URL | `postgresql+asyncpg://ledgerlite:<pw>@10.82.0.3:5432/ledgerlite` |

> **Security note:** Never put these values in any committed file. They live only in GitHub Environments. The staging values differ from production values.

## 3. Generate the KUBECONFIG secret

Run this locally after authenticating with gcloud:

```bash
# Staging
gcloud container clusters get-credentials ledgerlite-staging \
  --region us-central1 \
  --project project-6737f3c2-e011-49b7-ae4

# Encode and copy to clipboard
cat ~/.kube/config | base64 | pbcopy
# Paste as the KUBECONFIG secret value in GitHub (staging environment)
```

Repeat for production when that cluster is created.

## 4. Trigger a Deploy

Go to: **GitHub → repo → Actions → Deploy → Run workflow**

Select the environment and click **Run workflow**. The workflow will:
1. Authenticate to GKE using the `KUBECONFIG` secret
2. Apply real secrets to the cluster (idempotent upsert)
3. Update service image tags to the new SHA
4. Run smoke tests against `/health` on all 8 services
5. Auto-rollback if any smoke test fails

## 5. cert-manager / TLS Setup (one-time, per cluster)

Before TLS certificates are issued, install cert-manager and apply the ClusterIssuers:

```bash
# Install cert-manager
kubectl apply -f https://github.com/cert-manager/cert-manager/releases/download/v1.16.3/cert-manager.yaml
kubectl wait --for=condition=Available deployment --all -n cert-manager --timeout=120s

# Apply ClusterIssuers (Let's Encrypt staging + production)
kubectl apply -k infrastructure/kubernetes/cert-manager/
```

After this, every `kubectl apply -k infrastructure/kubernetes/overlays/staging` will automatically:
- Request a certificate from Let's Encrypt staging
- Configure HTTPS on the nginx ingress
- Store the TLS cert in the `ledgerlite-tls-staging` secret

Switch to `letsencrypt-prod` issuer in the production overlay when ready for a trusted certificate.
