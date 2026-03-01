# LedgerLite — Full Context (Complete Restart File)
_Last updated: Sprint 6C complete. Written to enable full session restart with zero prior context._

---

## 1. What Is This Product

**LedgerLite** — Mobile-first accounting and ledger SaaS for households and small businesses in India/SEA.
- Track income/expenses, manage accounts, run reports
- Business ledger: track customer credit (who owes what)
- Offline-first mobile app with background sync
- AI-assisted categorization, receipt OCR stub

**Target users:** Shop owners, households, small businesses — India/SEA market.

---

## 2. Monorepo Layout

```
/Users/santhoshsrinivas/MyApps/iLedgerLite/
├── apps/
│   ├── mobile-app/          # Flutter (Dart) — 43 files, 5-tab app
│   └── web-dashboard/       # Next.js 14 — 6 tabs (TypeScript, Recharts, TanStack, Zustand)
├── services/
│   ├── auth-service/        # Port 8001 — JWT login/register/refresh
│   ├── user-service/        # Port 8002 — profiles, settings, onboarding
│   ├── transaction-service/ # Port 8003 — transactions, accounts, categories
│   ├── ledger-service/      # Port 8004 — customers, ledger entries, credit tracking
│   ├── report-service/      # Port 8005 — P&L, cashflow, budget, export
│   ├── ai-service/          # Port 8006 — categorize, insights, OCR stub
│   ├── notification-service/# Port 8007 — notifications, reminders
│   └── sync-service/        # Port 8008 — push/pull offline sync
├── database/
│   ├── schema.sql           # Canonical schema (source of truth)
│   ├── seeds/categories.sql # 29 system categories
│   └── migrations/          # Alembic (2 migrations: schema + seeds)
├── infrastructure/
│   ├── kubernetes/          # Kustomize base + staging/production overlays (23 files)
│   └── terraform/           # GCP IaC — Sprint 6C (25 files, 6 modules)
├── .github/workflows/       # test.yml, lint.yml, build.yml, deploy.yml
├── memory/
│   ├── MEMORY.md            # Always-loaded summary (pointer file)
│   └── full-context.md      # This file
├── CLAUDE.md                # Coding conventions (always read first)
├── ROADMAP.md               # Sprint status
└── docs/
    ├── API.md
    └── SPRINT-LOG.md
```

---

## 3. Tech Stack

| Layer | Tech |
|-------|------|
| Mobile | Flutter/Dart, Riverpod, Dio, SQLite (sqflite), flutter_secure_storage |
| Web | Next.js 14, TypeScript, TanStack Query, Zustand, Recharts |
| Backend | Python 3.12, FastAPI, SQLAlchemy (async), Pydantic v2, python-jose, bcrypt |
| Database | PostgreSQL 16 (primary), Redis 7 (cache/sessions) |
| Infra | Docker Compose (dev), Kubernetes + Kustomize (prod), Terraform (GCP) |
| CI/CD | GitHub Actions — test/lint/build/deploy |

---

## 4. All Sprints — What Was Built

| Sprint | Deliverable | Status |
|--------|-------------|--------|
| 0 | auth-service (4 endpoints, 15 tests) | Done |
| 1 | user-service (5 endpoints, 18 tests) + shared/ | Done |
| 2 | transaction-service (12 endpoints, 27 tests) + DB seeds | Done |
| 3 | ledger-service (7 endpoints, 26 tests) | Done |
| 4 | report-service (5 ep, 18 tests) + notification-service (3 ep, 12 tests) | Done |
| Retro 4.5 | CI/CD hardening (test + lint + build + deploy workflows) | Done |
| 5 | sync-service (3 ep, 14 tests) + ai-service (3 ep, 16 tests) | Done |
| 6A | Alembic migrations (initial schema + seeds) | Done |
| 6B | Kubernetes manifests — Kustomize base + staging/prod overlays (23 files) | Done |
| 6C | Terraform IaC for GCP (25 files, 6 modules) | **Done — not yet deployed** |
| 7 | Flutter mobile: auth, dashboard, transactions, accounts | Done |
| 8 | Flutter mobile: ledger, reports, offline sync, settings (43 total Dart files) | Done |
| 9 | Next.js web dashboard (6 tabs: dashboard, transactions, accounts, ledger, reports, analytics) | Done |

**Total: 146 tests across 8 services. All code written. GCP not yet provisioned.**

---

## 5. GCP Configuration

| Item | Value |
|------|-------|
| Project ID | `project-6737f3c2-e011-49b7-ae4` |
| Region | `us-central1` |
| Terraform state bucket | `gs://project-6737f3c2-e011-49b7-ae4-tf-state` (create before `terraform init`) |
| GKE cluster (staging) | `ledgerlite-staging` |
| GKE cluster (production) | `ledgerlite-production` |
| GCS receipts bucket (staging) | `ledgerlite-staging-receipts-project-6737f3c2-e011-49b7-ae4` |
| App service account (staging) | `ledgerlite-staging-app@project-6737f3c2-e011-49b7-ae4.iam.gserviceaccount.com` |

---

## 6. Terraform — All Files Created This Session

### Root files
| File | Purpose |
|------|---------|
| `infrastructure/terraform/backend.tf` | GCS remote state — bucket: `project-6737f3c2-e011-49b7-ae4-tf-state` |
| `infrastructure/terraform/main.tf` | Provider config, enable 7 GCP APIs, wire all 6 modules |
| `infrastructure/terraform/variables.tf` | `project_id`, `region`, `environment`, `db_password` (sensitive) |
| `infrastructure/terraform/outputs.tf` | Cluster name/endpoint, Cloud SQL IP, Redis URL, bucket name, kubectl cmd |
| `infrastructure/terraform/.gitignore` | Exclude `*.tfstate`, `.terraform/`, `*.tfvars.backup`, `*.auto.tfvars` |
| `infrastructure/terraform/envs/staging.tfvars` | `project_id`, `region=us-central1`, `environment=staging` |
| `infrastructure/terraform/envs/production.tfvars` | `project_id`, `region=us-central1`, `environment=production` |

### Module: vpc (3 files)
`infrastructure/terraform/modules/vpc/`
- **Creates:** VPC (`ledgerlite-{env}-vpc`), GKE subnet (`10.0.0.0/20`, secondary ranges pods=`10.16.0.0/14` services=`10.20.0.0/20`), private service peering for Cloud SQL/Memorystore, internal firewall rule, health-check firewall rule
- **Conditional:** Cloud Router + Cloud NAT — **production only** (saves ~$32/mo for staging)

### Module: gke (3 files)
`infrastructure/terraform/modules/gke/`
- **Creates:** Standard GKE cluster (not Autopilot) + managed node pool, Workload Identity enabled
- **Staging:** 1 preemptible `e2-medium` node, public nodes (no private cluster config)
- **Production:** 2 `e2-standard-2` nodes, private cluster (`172.16.0.0/28` master CIDR), `deletion_protection=true`
- **Variables:** `enable_private_nodes`, `node_count`, `machine_type`, `preemptible`

### Module: cloudsql (3 files)
`infrastructure/terraform/modules/cloudsql/`
- **Creates:** Postgres 16 instance (private IP only, SSL `ENCRYPTED_ONLY`), database `ledgerlite`, user `ledgerlite`
- **Staging:** `db-f1-micro`, ZONAL, 20GB SSD, 7-day backups, `deletion_protection=false`
- **Production:** `db-custom-2-7680`, REGIONAL HA, 50GB SSD, 30-day backups + PITR, `deletion_protection=true`

### Module: memorystore (3 files)
`infrastructure/terraform/modules/memorystore/`
- **Creates:** Redis 7 — **production only** (`count = var.env == "production" ? 1 : 0`)
- **Production only:** 2GB STANDARD_HA, AUTH enabled
- **Staging:** `count=0` — uses in-cluster Redis pod (already in K8s base manifests)
- **Outputs:** conditional — returns empty string for staging

### Module: storage (3 files)
`infrastructure/terraform/modules/storage/`
- **Creates:** GCS bucket for receipts, lifecycle rule (NEARLINE after 365 days), CORS config
- **Versioning:** enabled for production only
- **IAM:** grants `roles/storage.objectAdmin` to app service account

### Module: iam (3 files)
`infrastructure/terraform/modules/iam/`
- **Creates:** App service account `ledgerlite-{env}-app`
- **Roles:** `cloudsql.client`, `logging.logWriter`, `monitoring.metricWriter`
- **Workload Identity binding:** `ledgerlite-staging-app` ↔ K8s SA `ledgerlite/ledgerlite-app`

---

## 7. Files Modified This Session

| File | What Changed |
|------|-------------|
| `infrastructure/kubernetes/overlays/staging/kustomization.yaml` | Added: delete in-cluster Postgres StatefulSet + Service patches; Updated secrets patch to include `REDIS_URL: redis://redis:6379` and `DATABASE_URL` with `CLOUD_SQL_PRIVATE_IP` placeholder |
| `infrastructure/terraform/modules/gke/main.tf` | Replaced Autopilot with Standard GKE + managed node pool, conditional private_cluster_config |
| `infrastructure/terraform/modules/gke/variables.tf` | Added: `enable_private_nodes`, `node_count`, `machine_type`, `preemptible` |
| `infrastructure/terraform/modules/gke/outputs.tf` | Updated resource reference from `.autopilot` to `.main` |
| `infrastructure/terraform/modules/vpc/main.tf` | Added Cloud NAT (then made it conditional — production only) |
| `infrastructure/terraform/modules/memorystore/main.tf` | Added `count = var.env == "production" ? 1 : 0` |
| `infrastructure/terraform/modules/memorystore/outputs.tf` | All outputs made conditional with `length(...)` check |
| `infrastructure/terraform/main.tf` | Added 4 new GKE variables to module call |
| `infrastructure/terraform/outputs.tf` | `redis_url` made conditional; `redis_host` description updated |
| `memory/MEMORY.md` | Created/updated (pointer file, always loaded) |

---

## 8. Architecture Decisions Made This Session

### Why Standard GKE over Autopilot
Autopilot charges ~$0.0445/vCPU-hr per pod + cluster management fee ($73/mo for 2nd cluster). Standard GKE with 1 preemptible e2-medium costs ~$10-15/mo total for staging. Saves ~$65/month.

### Why no private nodes for staging
Private nodes require Cloud NAT (~$32/month). Staging doesn't need production-grade security. Public nodes are fine for dev/test. Production keeps private nodes for security.

### Why in-cluster Redis for staging
Memorystore BASIC costs ~$35/month. The K8s base manifests already deploy a Redis pod. Staging uses it for free. Production uses managed Memorystore for HA and reliability.

### Why keep Cloud SQL for staging (not in-cluster Postgres)
Data persistence matters even for staging — you don't want to lose test data on pod restarts. Cloud SQL db-f1-micro is $10/month and gives real managed Postgres behaviour.

### Why GCS backend for Terraform state
Remote state is essential for team use and prevents state corruption. The state bucket must be created manually before `terraform init`.

---

## 9. Cost Analysis

### Staging (~$44/month)
| Item | Cost | Notes |
|------|------|-------|
| GKE Standard (1 preemptible e2-medium) | ~$10-15 | First cluster = free management fee |
| Cloud SQL db-f1-micro | ~$10 | Cheapest Postgres tier |
| Memorystore | $0 | Skipped — in-cluster Redis |
| Cloud NAT | $0 | Skipped — no private nodes |
| HTTP(S) Load Balancer | ~$18 | Created by nginx ingress |
| GCS | ~$1 | Negligible |
| **Total** | **~$39-44** | |

### Production (~$650-850/month)
| Item | Cost | Notes |
|------|------|-------|
| GKE Standard (2x e2-standard-2) | ~$160-200 | + $73 cluster fee (2nd cluster) |
| Cloud SQL db-custom-2-7680 REGIONAL HA | ~$200-220 | HA doubles the cost |
| Memorystore Redis 2GB STANDARD_HA | ~$160 | HA standby replica |
| Cloud NAT | ~$32 | Required for private nodes |
| HTTP(S) Load Balancer | ~$18 | |
| GCS | ~$5 | |
| **Total** | **~$650-850** | |

### Hidden costs to watch
- **Egress:** $0.085-0.12/GB out to internet — scales with users
- **Cloud Logging:** Free up to 50GB/month; $0.01/GB after (8 verbose services)
- **Preemptible node restarts:** Staging node can be terminated with 30s notice; GKE auto-replaces it (~2min downtime)

---

## 10. Kubernetes Setup (existing, not changed this session)

### Base manifests (`infrastructure/kubernetes/base/`)
- `namespace.yaml` — `ledgerlite` namespace
- `configmap.yaml` — `JWT_ALGORITHM=HS256`
- `secret.yaml` — `ledgerlite-secrets` (JWT_SECRET, DATABASE_URL, DATABASE_USER, DATABASE_PASSWORD)
- `ingress.yaml` — nginx-ingress, 12 path-based routes (one per service)
- `migrations-job.yaml` — Alembic job, image: `ghcr.io/sunnysans/ledgerlite/migrations:latest`, reads DATABASE_URL from secret
- `postgres/statefulset.yaml` + `service.yaml` — in-cluster Postgres (removed in staging overlay)
- `redis/deployment.yaml` + `service.yaml` — in-cluster Redis 7 (kept for staging, service name: `redis`, port: 6379)
- `services/<name>-service.yaml` — Deployment + Service for each of 8 microservices

### Staging overlay (`infrastructure/kubernetes/overlays/staging/`)
Patches applied on top of base:
1. Namespace renamed to `ledgerlite-staging`
2. Ingress host → `api.staging.ledgerlite.app`
3. **Delete** in-cluster Postgres StatefulSet + Service
4. Secrets: `DATABASE_URL` points to Cloud SQL IP (placeholder: `CLOUD_SQL_PRIVATE_IP`), `REDIS_URL=redis://redis:6379`
5. Image tags: all 8 services → `ghcr.io/sunnysans/ledgerlite/<service>:staging`

### Production overlay (`infrastructure/kubernetes/overlays/production/`)
- 2 replicas per service
- Production image tags
- Production secrets (need updating when deploying)

---

## 11. Complete Staging Deployment Guide

### Prerequisites
```bash
brew install terraform kubectl google-cloud-sdk
gcloud auth application-default login
gcloud config set project project-6737f3c2-e011-49b7-ae4
```

### One-time: Create Terraform state bucket
```bash
gcloud storage buckets create gs://project-6737f3c2-e011-49b7-ae4-tf-state \
  --project=project-6737f3c2-e011-49b7-ae4 \
  --location=us-central1
```

### Terraform apply
```bash
cd infrastructure/terraform
terraform init
export TF_VAR_db_password="choose-strong-password"   # store this safely
terraform apply -var-file=envs/staging.tfvars
# Takes ~10-15 min (GKE cluster is the slow part)
```
After apply, copy these outputs:
- `cloudsql_private_ip`
- `connect_to_cluster` (kubectl command)
- `receipts_bucket_name`
- `app_service_account_email`

### Update K8s staging secrets
Edit `infrastructure/kubernetes/overlays/staging/kustomization.yaml`:
```yaml
DATABASE_URL: "postgresql+asyncpg://ledgerlite:<TF_VAR_db_password>@<cloudsql_private_ip>:5432/ledgerlite"
DATABASE_PASSWORD: "<TF_VAR_db_password>"
JWT_SECRET: "<generate with: openssl rand -hex 32>"
REDIS_URL: "redis://redis:6379"   # already set, leave as-is
```

### Connect kubectl
```bash
# Use the exact command from terraform output "connect_to_cluster"
gcloud container clusters get-credentials ledgerlite-staging \
  --region us-central1 --project project-6737f3c2-e011-49b7-ae4
```

### GHCR pull secret (only if packages are private)
```bash
kubectl create namespace ledgerlite-staging  # may already exist
kubectl create secret docker-registry ghcr-pull-secret \
  --docker-server=ghcr.io \
  --docker-username=sunnysans \
  --docker-password=<GITHUB_PAT_read:packages> \
  -n ledgerlite-staging
```
If needed, add to each service deployment in staging overlay:
```yaml
spec:
  template:
    spec:
      imagePullSecrets:
        - name: ghcr-pull-secret
```

### Deploy
```bash
kubectl apply -k infrastructure/kubernetes/overlays/staging
```

### Monitor migrations (must complete before services are healthy)
```bash
kubectl get jobs -n ledgerlite-staging
kubectl logs -l app.kubernetes.io/name=ledgerlite-migrations -n ledgerlite-staging -f
```

### Verify
```bash
kubectl get pods -n ledgerlite-staging          # all should be Running
kubectl get ingress -n ledgerlite-staging        # get external LB IP

LB_IP=$(kubectl get ingress ledgerlite-ingress -n ledgerlite-staging \
  -o jsonpath='{.status.loadBalancer.ingress[0].ip}')

curl http://$LB_IP/auth/health
curl http://$LB_IP/users/health
curl http://$LB_IP/transactions/health
curl http://$LB_IP/ledger/health
curl http://$LB_IP/reports/health
curl http://$LB_IP/ai/health
curl http://$LB_IP/notifications/health
curl http://$LB_IP/sync/health
```

---

## 12. Production Deployment (after staging is validated)

Same steps as staging but:
```bash
terraform apply -var-file=envs/production.tfvars
kubectl apply -k infrastructure/kubernetes/overlays/production
```
Update `infrastructure/kubernetes/overlays/production/kustomization.yaml` with:
- Cloud SQL private IP (production instance)
- Strong JWT_SECRET
- DATABASE_PASSWORD
- REDIS_URL: `redis://<memorystore_host>:6379` (from `terraform output redis_url`)

**Production DNS:**
- `api.ledgerlite.app` → production ingress LB IP
- `api.staging.ledgerlite.app` → staging ingress LB IP
Set these in your DNS provider (Cloudflare, GoDaddy, etc.)

**Update GitHub Actions deploy workflow** to use:
```
gcloud container clusters get-credentials ledgerlite-production --region us-central1
```

---

## 13. Known Issues & Gotchas

| Issue | Detail | Fix |
|-------|--------|-----|
| `CLOUD_SQL_PRIVATE_IP` placeholder | Staging kustomization has literal placeholder | Replace after `terraform output cloudsql_private_ip` |
| Preemptible node restarts | Staging node can be evicted with 30s notice; all pods restart | Acceptable for staging; auto-replaces in ~2 min |
| Migrations job runs on every `kubectl apply` | Job has `ttlSecondsAfterFinished: 300` — it cleans itself up | Alembic is idempotent so re-running is safe |
| Cloud SQL private IP requires VPC peering | `google_service_networking_connection` must complete before Cloud SQL is usable | Handled via `depends_on = [module.vpc]` in Terraform |
| Second GKE cluster costs $73/month | Management fee for non-free-tier cluster | First cluster per billing account is free. Staging = free. Production = $73/mo |
| In-cluster Redis has no persistence on staging | Redis pod uses `appendonly yes` but data lost if pod is evicted | Acceptable for staging — cache only |
| Workload Identity binding | `iam.tf` binds `project-id.svc.id.goog[ledgerlite/ledgerlite-app]` K8s SA | If namespace differs, update the binding member string in `modules/iam/main.tf` |

---

## 14. Backend Coding Conventions (critical, from CLAUDE.md)

- **UUID columns:** Always `from sqlalchemy import Uuid` + `mapped_column(Uuid, ...)`. NEVER `postgresql.UUID(as_uuid=True)` — breaks SQLite test backend
- **Async SQLAlchemy:** Always `selectinload()` for relationships, never lazy load. Use `populate_existing=True` after mutations
- **Password hashing:** `bcrypt` directly. NOT passlib (incompatible with bcrypt>=5.0)
- **JWT:** `python-jose` HS256. Tokens have `type` claim (`"access"` or `"refresh"`)
- **Monetary amounts:** `Numeric(15, 2)`. Never float
- **Soft delete:** `is_active=False`. Never hard-delete user records
- **Test DB:** SQLite + aiosqlite in-memory. `asyncio_mode = auto` in pytest.ini

---

## 15. Post-MVP Roadmap (Phase 2+)

- OTP/phone login (replace email for India market)
- Bank SMS parsing → auto-import transactions
- UPI payment integration
- Voice transaction entry
- Multi-language: Hindi, Tamil, Telugu
- Family/shared household ledger
- Budget planner with alerts
- Receipt OCR (Google Vision / Tesseract)
- AI categorization (real ML model)
- Cashflow forecasting
- RBAC / accountant access portal
- GST-ready tax reports
- iOS app release
- Embedded finance: credit lines, BNPL, insurance recommendations
