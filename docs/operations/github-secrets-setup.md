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

## 6. Staging CI — GCP Auth via Workload Identity Federation (WIF)

The GCP workflows (staging-start, staging-stop, cost-snapshot) authenticate using
**Workload Identity Federation** — no long-lived JSON keys, no `GCP_SA_KEY` secret.
GitHub Actions exchanges an OIDC token for short-lived GCP credentials automatically.

The `ledgerlite-ci` service account has the minimum required roles:

| Role | Why |
|---|---|
| `roles/container.admin` | Resize GKE node pool (scale to 0 / restore) |
| `roles/cloudsql.admin` | Patch Cloud SQL activation policy (ALWAYS / NEVER) |

### Infrastructure (already configured — do not repeat)

The WIF pool and provider were set up manually in Sprint 14:

```bash
# Workload Identity Pool: github-actions (global)
# Provider: github (GitHub OIDC — scoped to sunnysanthosh/iLedgerLite only)
# SA binding: principalSet for this repo → roles/iam.workloadIdentityUser on ledgerlite-ci
```

If you ever need to recreate it (e.g. new GCP project):

```bash
export PATH="/opt/homebrew/share/google-cloud-sdk/bin:$PATH"
PROJECT=project-6737f3c2-e011-49b7-ae4
PROJECT_NUMBER=1077475679584
REPO="sunnysanthosh/iLedgerLite"
SA="ledgerlite-ci@${PROJECT}.iam.gserviceaccount.com"

# Create pool + provider
gcloud iam workload-identity-pools create "github-actions" \
  --project="$PROJECT" --location="global" --display-name="GitHub Actions"

gcloud iam workload-identity-pools providers create-oidc "github" \
  --project="$PROJECT" --location="global" \
  --workload-identity-pool="github-actions" \
  --issuer-uri="https://token.actions.githubusercontent.com" \
  --attribute-mapping="google.subject=assertion.sub,attribute.repository=assertion.repository" \
  --attribute-condition="assertion.repository=='${REPO}'"

# Bind SA
gcloud iam service-accounts add-iam-policy-binding "$SA" \
  --project="$PROJECT" \
  --role="roles/iam.workloadIdentityUser" \
  --member="principalSet://iam.googleapis.com/projects/${PROJECT_NUMBER}/locations/global/workloadIdentityPools/github-actions/attribute.repository/${REPO}"

# Set GitHub secrets
gh secret set WIF_PROVIDER --body "projects/${PROJECT_NUMBER}/locations/global/workloadIdentityPools/github-actions/providers/github"
gh secret set WIF_SERVICE_ACCOUNT --body "$SA"
```

### GitHub secrets (already set)

| Secret name | Value | Set by |
|---|---|---|
| `WIF_PROVIDER` | `projects/1077475679584/locations/global/workloadIdentityPools/github-actions/providers/github` | Sprint 14 setup |
| `WIF_SERVICE_ACCOUNT` | `ledgerlite-ci@project-6737f3c2-e011-49b7-ae4.iam.gserviceaccount.com` | Sprint 14 setup |

### Verify the workflow runs

Go to: **GitHub → repo → Actions → Staging — Stop → Run workflow**

A successful run will:
1. Authenticate to GCP via WIF OIDC (no secrets on disk)
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
| `staging-start.yml` | (repo-level) | `WIF_PROVIDER`, `WIF_SERVICE_ACCOUNT` |
| `staging-stop.yml` | (repo-level) | `WIF_PROVIDER`, `WIF_SERVICE_ACCOUNT` |
| `cost-snapshot.yml` | (repo-level) | `WIF_PROVIDER`, `WIF_SERVICE_ACCOUNT` (optional — degrades gracefully) |
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
