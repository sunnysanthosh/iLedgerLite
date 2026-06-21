# Environment Lifecycle — On-Demand Best Practice

> **Core principle:** Every environment is on-demand. Start before a session, stop when done.
> No environment should idle overnight burning compute you are not using.

This document establishes the on-demand environment lifecycle as a team standard across all
three tiers — local dev, staging (GCP), and production (GCP). It is the entry point for
onboarding any new engineer onto the infrastructure workflow.

---

## Why On-Demand?

| Problem | Impact |
|---|---|
| Dev containers left running overnight | ~8 GB RAM + CPU held on your laptop for nothing |
| Staging GKE nodes always-on | ~$45/month compute wasted when no one is testing |
| Cloud SQL always-on in staging | ~$15/month + storage even with zero queries |

**Total avoidable waste at current scale: $22–$39/month on staging alone.**
As we add environments (UAT, feature branches), this compounds quickly.
The on-demand model costs $0 extra in tooling — it is pure discipline enforced by automation.

---

## The Three Tiers

```
┌─────────────────────────────────────────────────────────────────┐
│  LOCAL DEV                                                      │
│  Docker Compose — Postgres + Redis + 8 FastAPI services         │
│  Start: make dev-start    Stop: make dev-stop                   │
│  Data:  volumes preserved across stop/start                     │
├─────────────────────────────────────────────────────────────────┤
│  STAGING  (GCP — us-central1)                                   │
│  GKE Standard + Cloud SQL db-f1-micro + nginx-ingress           │
│  Start: GitHub Actions → Staging — Start (manual or pre-deploy) │
│  Stop:  Automatic nightly at 22:00 UTC (03:30 IST) via cron     │
│  Data:  Cloud SQL storage preserved (activation-policy=NEVER)   │
├─────────────────────────────────────────────────────────────────┤
│  PRODUCTION  (GCP — us-central1)                                │
│  GKE Regional + Cloud SQL REGIONAL + Memorystore HA             │
│  Always-on — never scaled to 0. HA by design.                   │
│  Deploy: GitHub Actions → Deploy → production (requires review) │
└─────────────────────────────────────────────────────────────────┘
```

---

## Quick Reference — Which Command to Use

| Situation | Command |
|---|---|
| Start a dev session | `make dev-start` |
| End a dev session (preserve data) | `make dev-stop` |
| Rebuild images after code/deps change | `make dev-rebuild` |
| Check what is running locally | `make dev-status` |
| Follow logs for all local services | `make dev-logs` |
| Clean slate (wipe local DB) | `make dev-reset` (confirms before running) |
| Run the 4-gate sprint test suite | `make test-e2e` — **local only, no cloud needed** |
| Start staging for a true E2E run against the deployed env | GitHub Actions → **Staging — Start** (zonal cluster, `us-central1-a`) |
| Start staging before a deploy | Staging starts automatically via `deploy.yml` |
| Stop staging immediately after the E2E run finishes | GitHub Actions → **Staging — Stop** (don't wait for the nightly cron) |
| Deploy to staging | GitHub Actions → **Deploy** → staging |
| Deploy to production | GitHub Actions → **Deploy** → production (requires review) |

---

## Bringing Up GCP — Step by Step

> **Stop and check first: have you run `make test-e2e` locally and had it pass?**
> If not, do that first. GCP is the *last* step in the testing chain, not a
> debugging tool — see "Where Do Tests Run?" below for the full policy.
> Everything in this section assumes local has already confirmed the change works.

### Staging (the common case)

**Preferred — GitHub Actions:** `Actions → Staging — Start → Run workflow`
([staging-start.yml](../../.github/workflows/staging-start.yml)). This is what
should be used for ~95% of bring-ups (pre-deploy checks, post-deploy E2E runs).
It starts Cloud SQL, scales the node pool, waits for nodes to be `Ready`, and
rolls out any pods stuck from the prior stop — all in one step.

**Manual (only when you need local `kubectl` access — e.g. debugging a deploy):**

```bash
export PATH="/opt/homebrew/share/google-cloud-sdk/bin:$PATH"

# 1. Start Cloud SQL
gcloud sql instances patch ledgerlite-staging-pg --activation-policy=ALWAYS

# 2. Scale the GKE node pool up — staging is a ZONAL cluster (us-central1-a)
gcloud container clusters resize ledgerlite-staging \
  --node-pool ledgerlite-staging-nodes --num-nodes 1 \
  --zone us-central1-a --quiet

# 3. Get kubectl credentials
gcloud container clusters get-credentials ledgerlite-staging \
  --zone us-central1-a --project project-6737f3c2-e011-49b7-ae4

# 4. Verify
kubectl get nodes
kubectl get pods -n ledgerlite-staging
```

**Immediately after your test session — tear it back down** (don't wait for the
22:00 UTC nightly cron):

```bash
# Scale node pool back to 0
gcloud container clusters resize ledgerlite-staging \
  --node-pool ledgerlite-staging-nodes --num-nodes 0 \
  --zone us-central1-a --quiet

# Stop Cloud SQL
gcloud sql instances patch ledgerlite-staging-pg --activation-policy=NEVER
```

Or just run **Staging — Stop** from GitHub Actions, which does the same thing.

> **Why `--zone` and not `--region`?** Staging was converted to a zonal cluster
> in `us-central1-a` to eliminate GKE's regional control-plane management fee
> (~$73/month, billed even at 0 nodes). A zonal cluster gets that fee waived
> under GCP's free tier (one zonal cluster per billing account). Production
> stays regional for control-plane HA — see below.

### Production

Production is **always-on and never scaled to 0** (see Rule 3 below) — there is
no routine "bring it up" step. The commands here apply only to **initial
provisioning** or **disaster recovery** (cluster lost/corrupted), and any
production change requires review per the CI/CD rules in `CLAUDE.md`:

```bash
export PATH="/opt/homebrew/share/google-cloud-sdk/bin:$PATH"

# Provision/recover the production GKE cluster (regional, multi-zone control plane)
cd infrastructure/terraform
terraform apply -target=module.gke -var-file=envs/production.tfvars

# Get kubectl credentials
gcloud container clusters get-credentials ledgerlite-production --region us-central1 \
  --project project-6737f3c2-e011-49b7-ae4
```

---

## Daily Workflow for Developers

### Start of day

```bash
# 1. Pull latest from your sprint branch
git pull

# 2. Start the local dev stack (waits for Postgres to be ready)
make dev-start

# 3. Activate Python venv for running tests or a single service
source .venv/bin/activate
```

### During development

```bash
# Run tests for the service you are working on
make test-auth           # or test-user, test-transaction, etc.

# Lint and format before committing
make lint
make format

# Watch logs if something is misbehaving
make dev-logs

# Check container health
make dev-status
```

### End of day

```bash
# Stop the stack — data is safe in Docker volumes
make dev-stop

# Deactivate venv
deactivate
```

---

## Environment Lifecycle State Machine

```
                   make dev-start
                  ┌─────────────┐
   Stopped ───────►   Running   ├───── make dev-stop ──────► Stopped
   (volumes       └──────┬──────┘      (volumes intact)      (volumes
    intact)              │                                     intact)
                         │ make dev-reset
                         │ (with confirmation)
                         ▼
                      Destroyed
                   (volumes wiped)
                         │
                         │ make dev-start
                         ▼
                      Running
                   (fresh DB from
                    schema.sql)
```

For staging the same model applies but the mechanism is GKE node resize + Cloud SQL
activation policy rather than Docker Compose.

---

## Cost Impact (Staging)

| Model | Active hrs/month | Compute | Fixed | Total |
|---|---|---|---|---|
| Always-on | 730 hrs | $45 | $26 | **$71/mo** |
| Nightly-off (current) | ~360 hrs | $23 | $26 | **~$49/mo** |
| Business-hours only | ~240 hrs | $15 | $26 | **~$41/mo** |
| CI-runs only (~3 hrs/day) | ~90 hrs | $6 | $26 | **~$32/mo** |

Fixed costs (Network LB $18, Cloud Router $7, GCS $1) cannot be avoided
regardless of on/off state. GKE cluster management is free for the first zonal cluster.

---

## Rules for the Team

1. **Never leave dev containers running overnight.** `make dev-stop` at the end of every session.
2. **Never leave staging running if no one is testing.** The nightly cron handles this automatically, but run `Staging — Stop` manually after a test session if it is mid-day.
3. **Never scale production to 0.** Production is always-on, always HA. The on-demand model applies only to dev and staging.
4. **Stopping ≠ deleting.** `make dev-stop` and `Staging — Stop` both preserve data. Nothing is lost.
5. **`make dev-reset` and `dev-rebuild` are different.** Reset wipes data. Rebuild only rebuilds images.
6. **Staging is for end-to-end runs only — everything else is local.** See "Where Do Tests Run?" below.

---

## Where Do Tests Run?

> **Default to local. Staging (GKE + Cloud SQL) is started only for a true end-to-end run
> against the deployed environment, and stopped again immediately afterward.**

| Test | Where | Command |
|---|---|---|
| Unit tests (per service) | Local — `.venv`, no Docker needed | `make test-auth`, `make test-user`, etc. |
| 4-gate sprint suite (schema + unit + smoke + regression) | Local — `.venv`, no Docker needed | `make test-e2e` |
| Manual API exploration / integration debugging | Local Docker Compose | `make dev-start` → hit `localhost:8001-8008` |
| **True end-to-end against the deployed staging stack** (post-deploy verification, pre-release sanity check) | **Staging (GCP)** — start it for this run only | `Staging — Start` → run the check → `Staging — Stop` |

Staging should sit at **0 GKE nodes / Cloud SQL stopped** the vast majority of the time. The
only reason to start it is to verify the *actual deployed* environment (ingress, TLS, real
Cloud SQL connectivity, K8s manifests) — something `make test-e2e` and Docker Compose
deliberately cannot do, since they run against local fixtures/SQLite-backed test sessions, not
the GKE cluster. Once that verification is done, stop staging immediately — don't leave it
running "just in case" and don't wait for the nightly cron.

---

## gcloud Quirks & Gotchas (learned the hard way)

These don't change *what* to do, but they explain confusing output you may see while
starting/stopping staging. Documented 2026-06-15 after a hibernation cycle surfaced all three
in one session.

| Symptom | What's actually happening | What to do |
|---|---|---|
| `gcloud container clusters list` returns 403 "This API method requires billing to be enabled" | The project's billing account got closed/detached (not a quota or auth issue) | Check `gcloud billing accounts list` / `gcloud billing projects describe <project>` for `billingEnabled: false`. Re-link the billing account, then retry — no code or config change needed. |
| `gcloud container clusters list` still shows `NUM_NODES: 1` (or stale count) right after a `resize --num-nodes 0` | The `NUM_NODES` column in `clusters list` is cached/stale, not authoritative | Verify the real node count with `gcloud compute instance-groups list` — all zonal managed instance groups for the node pool should show 0 instances. |
| `gcloud sql instances patch --activation-policy=ALWAYS` (or `NEVER`) exits 1 client-side with "Operation ... is taking longer than expected", instance shows `MAINTENANCE` for 10-20 min | The client gives up polling before the server-side operation finishes; the start/stop itself usually succeeds | Don't retry immediately. Poll `gcloud sql instances describe <name>` until `state: RUNNABLE` (or `STOPPED`), then proceed. |
| Retrying a `gcloud sql instances patch` immediately returns 409 "another operation was already in progress" | The previous patch operation is still running server-side | Wait for `gcloud sql instances describe` to show no pending operation / a stable `RUNNABLE` state, then retry. |

---

## Related Documents

| Document | Purpose |
|---|---|
| [local-dev-guide.md](local-dev-guide.md) | Complete local dev command reference + troubleshooting |
| [github-secrets-setup.md](github-secrets-setup.md) | One-time setup: GitHub Environments, secrets, CI SA, cert-manager |
| [../../ROADMAP.md](../../ROADMAP.md) | Cloud cost baseline and sprint-exit cost snapshot table |
| [../../Makefile](../../Makefile) | All `make dev-*` and `make test-*` targets |
| [../../.github/workflows/staging-start.yml](../../.github/workflows/staging-start.yml) | Staging start workflow source |
| [../../.github/workflows/staging-stop.yml](../../.github/workflows/staging-stop.yml) | Staging stop workflow source (nightly cron) |
