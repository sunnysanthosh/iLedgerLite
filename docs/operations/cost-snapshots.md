# Sprint Cost Snapshots

> Captured at each sprint tag by the `cost-snapshot.yml` workflow (auto) or manually.
> GCP_SA_KEY was not configured in CI until Sprint 15, so Sprints 11–14 were captured manually.
> Review after each sprint to track infrastructure spend trends.

| Date | Sprint Tag | GKE Nodes | SQL Tier | SQL State | Notes |
|---|---|---|---|---|---|
| 2026-03-02 | sprint-11-done | 3 | db-f1-micro | RUNNABLE | Baseline — Sprint 11 exit; always-on |
| 2026-03-02 | sprint-12-done | 3 | db-f1-micro | RUNNABLE | manual capture; nightly-stop cron not working (GCP_SA_KEY missing) |
| 2026-03-14 | sprint-13-rbac-baseline | 3 | db-f1-micro | RUNNABLE | manual capture; always-on (nightly-stop still failing) |
| 2026-03-22 | sprint-14-done | 3 | db-f1-micro | RUNNABLE | manual capture; **hibernated same day** — GKE=0, SQL=STOPPED |
| 2026-04-05 | sprint-15-done |  | db-f1-micro | STOPPED | auto-captured |
| 2026-04-05 | sprint-16-done |  | db-f1-micro | STOPPED | auto-captured |
| 2026-05-02 | sprint-17-permissions-done |  | db-f1-micro | STOPPED | auto-captured |
| 2026-06-14 | sprint-17-done | err | db-f1-micro | STOPPED | auto-captured `err` on GKE nodes is **billing disabled** on project `project-6737f3c2-e011-49b7-ae4` — billing account `01A637-1B4A4F-58C83D` shows `OPEN: False`. `gcloud container clusters list` returns 403 (billing required). Actual spend is $0, but `staging-start.yml` / any GCP API call will fail until billing is re-enabled — needs investigation before next deploy. |
| 2026-06-15 | sprint-17-done | 1 | db-f1-micro | STOPPED | manual capture; **billing re-enabled** (`billingEnabled: true`). GKE cluster `ledgerlite-staging` is `RUNNING` with 1 node (e2-medium) — compute cost now accruing. Cloud SQL still `STOPPED` — services can't reach Postgres until it's started too. |
