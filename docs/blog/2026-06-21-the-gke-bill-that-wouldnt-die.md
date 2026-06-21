# The GKE Bill That Wouldn't Die

*2026-06-21 — LedgerLite engineering notes*

We "hibernate" staging every night — scale the GKE node pool to zero, stop
Cloud SQL. Standard cost hygiene for a side-project-scale SaaS. So when a
GCP billing report showed a steady ~₹7k/month Kubernetes Engine line item
running straight through a month where staging supposedly had *zero
compute nodes*, something didn't add up.

## The bug: regional vs. zonal

Our Terraform module set the cluster's `location` to the GCP **region**
(`us-central1`), not a zone. That's a meaningful distinction in GKE:

- A **zonal** cluster has its control plane in one zone. GCP waives the
  control-plane management fee for the first zonal cluster per billing
  account — it's effectively free.
- A **regional** cluster runs its control plane across three zones for HA.
  That costs a flat ~$0.10/hour, **24/7, regardless of node count** — and
  it's never eligible for the free-tier waiver.

We'd built staging with the same module as production, just with different
node counts and machine types. Nobody had separately considered whether
staging — which has no uptime requirement and gets scaled to zero every
night — needed regional control-plane HA at all. It didn't. Scaling nodes
to zero killed the *compute* bill; it did nothing for the *control plane*
bill, because that fee doesn't care how many nodes are running.

**Lesson:** "scaled to zero" and "costs zero" are different claims. Always
check what's actually billed per-resource, not just per-node.

## Fixing it meant destroying the cluster

GKE's `location` field is immutable — you can't migrate a regional cluster
to zonal in place. The fix was a real `terraform apply` that destroyed and
recreated the staging cluster. Since staging is stateless infrastructure
(workloads get redeployed from images + manifests, not hand-configured),
this was safe — but it's worth saying out loud: this class of fix is not a
no-op edit. It's a rebuild.

## The apply died halfway through

Mid-rebuild, with the *old* cluster already destroyed and the *new* one not
yet created, Terraform hit an unrelated error: a `google_service_account`
resource that existed in GCP but wasn't tracked in Terraform state (likely
created manually at some point, outside `terraform apply`). For a few
minutes, staging had **no GKE cluster at all** — not hibernated, just gone.

The fix was a `terraform import` to bring the drifted resource into state,
then re-running the apply to actually create the new cluster. No data was
lost (staging is stateless), but it's a sharp reminder that infrastructure
drift — resources that exist in the cloud but not in your IaC state — turns
into a landmine exactly when you're mid-change and can least afford a
surprise. A `terraform plan` *before* the destructive step would have
surfaced this ahead of time instead of mid-rebuild.

## A trail of `--region` flags

The cluster's location wasn't just one line in `main.tf`. Every place that
talked to the staging cluster by name had hardcoded `--region us-central1`:
two CI workflows (start/stop), a cost-snapshot job, a deploy-workflow
comment, two ops docs, and two memory files. None of these would have
*failed loudly* — `gcloud` with the wrong location flag for a cluster that
no longer exists at that location just returns "not found," which looks
like a transient error, not a configuration bug. Tracked all of them down
with a single `grep -rl "region us-central1"` across the repo rather than
trusting memory of "everywhere this might be referenced."

**Lesson:** when a piece of infrastructure identity changes (region → zone,
hostname, project ID), grep for the literal string across the whole repo,
not just the file you were editing. Docs and CI scripts rot silently.

## Built a test suite for the thing we just learned we weren't testing

While documenting the fix, a gap became obvious: the existing 4-gate local
test suite (`make test-e2e`) runs entirely against SQLite and in-process
ASGI clients. It is *structurally incapable* of catching this class of
problem — wrong ingress routing, a TLS cert that doesn't validate, a
`JWT_SECRET` that got applied to seven of eight deployed services instead of
all eight, a `DATABASE_URL` pointing at an unreachable Cloud SQL instance.
None of that exists until code is actually deployed.

So we added `tests/cloud/` — a small, separate pytest suite that makes real
HTTP calls over the public internet to a deployed environment. It logs in
through the real ingress, validates the JWT against three different
deployed services, writes a transaction to real Cloud SQL, and reads it
back. It's deliberately *not* part of `make test-e2e`, and it only runs via
a manual `workflow_dispatch` GitHub Action — it must never run against a
possibly-stopped staging cluster on every PR.

**Lesson:** local test suites and cloud verification answer different
questions. "Does the code work?" is answerable locally. "Did the deployment
actually wire everything together correctly?" is not — and conflating the
two either makes your local suite slow and flaky (if you make it hit real
cloud resources) or leaves a real gap (if you don't test deployment wiring
at all). Keeping them as two separate, explicitly-invoked suites was the
right call.

## Recap

| Problem | Root cause | Fix |
|---|---|---|
| Staging GKE cost money even at 0 nodes | Regional cluster control-plane fee, billed regardless of node count | Convert to zonal cluster (one-time destroy/recreate) |
| Mid-fix outage (no cluster for ~10 min) | Untracked IAM drift blocked the apply after old cluster was destroyed | `terraform import` the drifted resource, retry |
| Stale `--region` references across CI/docs | Infra identity change wasn't grepped across the whole repo | Repo-wide search + fix, not just the file being edited |
| No way to verify a deployment actually works end-to-end | Local suite only exercises SQLite/in-process code paths | New `tests/cloud/` suite, manual-only, separate from `test-e2e` |

Two PRs, one cost bug fixed, one capability gap closed.
