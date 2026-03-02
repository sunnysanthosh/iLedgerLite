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
| Start staging before a test run | GitHub Actions → **Staging — Start** |
| Start staging before a deploy | Staging starts automatically via `deploy.yml` |
| Stop staging early (before nightly cron) | GitHub Actions → **Staging — Stop** |
| Deploy to staging | GitHub Actions → **Deploy** → staging |
| Deploy to production | GitHub Actions → **Deploy** → production (requires review) |

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
