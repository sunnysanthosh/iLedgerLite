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
