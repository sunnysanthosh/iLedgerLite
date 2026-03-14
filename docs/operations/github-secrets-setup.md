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

## 6. Staging CI Service Account — `GCP_SA_KEY` (for Start/Stop workflows)

The [staging-start.yml](../../.github/workflows/staging-start.yml) and
[staging-stop.yml](../../.github/workflows/staging-stop.yml) workflows authenticate to GCP
using a dedicated CI service account (`ledgerlite-ci`). This SA is created by Terraform
(staging only) and has the minimum permissions required:

| Role | Why |
|---|---|
| `roles/container.admin` | Resize GKE node pool (scale to 0 / restore) |
| `roles/cloudsql.admin` | Patch Cloud SQL activation policy (ALWAYS / NEVER) |

### One-time setup (after `terraform apply` on staging)

```bash
# 1. Find the CI SA email (output from terraform)
cd infrastructure/terraform
terraform output -raw ci_service_account_email
# → ledgerlite-ci@project-6737f3c2-e011-49b7-ae4.iam.gserviceaccount.com

# 2. Create a JSON key for the SA
gcloud iam service-accounts keys create /tmp/ledgerlite-ci-key.json \
  --iam-account="ledgerlite-ci@project-6737f3c2-e011-49b7-ae4.iam.gserviceaccount.com" \
  --project="project-6737f3c2-e011-49b7-ae4"

# 3. Copy the key content (it is already JSON — no base64 needed)
cat /tmp/ledgerlite-ci-key.json | pbcopy

# 4. Delete the local key file immediately (it is sensitive)
rm /tmp/ledgerlite-ci-key.json
```

### Add to GitHub staging environment

Go to: **GitHub → repo → Settings → Environments → staging → Add secret**

| Secret name | Value |
|---|---|
| `GCP_SA_KEY` | Paste the JSON key content from step 3 |

> Do NOT add `GCP_SA_KEY` to the `production` environment — the CI SA is staging-only.
> Production GKE is always-on and should never be scaled to 0 from CI.

### Verify the workflow runs

Go to: **GitHub → repo → Actions → Staging — Stop → Run workflow**

A successful run will:
1. Authenticate to GCP using `GCP_SA_KEY`
2. Scale the `ledgerlite-staging-nodes` node pool to 0
3. Set Cloud SQL `ledgerlite-staging-pg` to `activation-policy=NEVER`
4. Print a summary of expected savings

Then run **Staging — Start** to restore the environment and confirm it recovers correctly.

### Nightly automatic stop

`staging-stop.yml` runs automatically on a cron schedule every night at **22:00 UTC (03:30 IST)**.
No manual action is needed — staging will stop itself after every working day.

To start staging for a test session:
- **GitHub → Actions → Staging — Start → Run workflow**
- Or: it starts automatically as part of the **Deploy** workflow before applying manifests.

---

## Summary: All Secrets by Workflow

| Workflow | Environment | Secrets used |
|---|---|---|
| `deploy.yml` | staging / production | `KUBECONFIG`, `DB_PASSWORD`, `JWT_SECRET`, `DATABASE_URL` |
| `staging-start.yml` | staging | `GCP_SA_KEY` |
| `staging-stop.yml` | staging | `GCP_SA_KEY` |
| `build.yml` | (repo-level) | `GITHUB_TOKEN` (automatic) |
| `test.yml` | (repo-level) | none |
| `lint.yml` | (repo-level) | none |

## 7. Slack Webhook — `SLACK_WEBHOOK_URL` (for CI failure alerts)

The `test.yml`, `lint.yml`, and `build.yml` workflows send a Slack message whenever a CI job fails.
The notification is **silently skipped** if the secret is not configured — no CI breakage.

### One-time setup

1. In Slack: **Apps → Incoming Webhooks → Add to Slack** → choose channel (e.g. `#ledgerlite-ci`) → copy the webhook URL
2. In GitHub: **repo → Settings → Secrets and variables → Actions → New repository secret**

| Secret name | Value |
|---|---|
| `SLACK_WEBHOOK_URL` | The Incoming Webhook URL from step 1 |

> Add as a **repository secret** (not environment-scoped) so alerts fire for any branch/PR.

### What the alert looks like

```
❌ Test suite failed — `Test` on `sprint-13/security-observability`
Repository   sunnysanthosh/iLedgerLite    Triggered by  sunnysanthosh
Commit       a1b2c3d                      Run           View failed run
```
