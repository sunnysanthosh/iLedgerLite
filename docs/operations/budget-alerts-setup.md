# GCP Budget Alerts Setup (TD-32)

> One-time setup. ~15 minutes. Prevents surprise bills.
> Configure immediately after reading this — costs can spike silently.

## Thresholds

| Environment | Warn at | Hard cap |
|---|---|---|
| Staging | $120 / month | $150 / month |
| Production | $520 / month | $650 / month |

---

## Option A — gcloud CLI (recommended)

```bash
export PROJECT_ID="project-6737f3c2-e011-49b7-ae4"
export BILLING_ACCOUNT=$(gcloud billing projects describe $PROJECT_ID \
  --format="value(billingAccountName)" | sed 's|billingAccounts/||')

# Staging budget — $150 cap, alert at $120 (80%) and $150 (100%)
gcloud billing budgets create \
  --billing-account="$BILLING_ACCOUNT" \
  --display-name="LedgerLite Staging" \
  --budget-amount=150USD \
  --threshold-rule=percent=0.8 \
  --threshold-rule=percent=1.0 \
  --filter-projects="projects/$PROJECT_ID" \
  --filter-labels="env=staging"

# Production budget — $650 cap, alert at $520 (80%) and $650 (100%)
gcloud billing budgets create \
  --billing-account="$BILLING_ACCOUNT" \
  --display-name="LedgerLite Production" \
  --budget-amount=650USD \
  --threshold-rule=percent=0.8 \
  --threshold-rule=percent=1.0 \
  --filter-projects="projects/$PROJECT_ID" \
  --filter-labels="env=production"
```

> **Note:** The `--filter-labels` flag filters by resource labels. Ensure GKE cluster and
> Cloud SQL have `env=staging` / `env=production` labels — these are set by Terraform's
> `env` variable and propagated through the GKE and CloudSQL modules.

---

## Option B — GCP Console

1. Go to: **Billing → Budgets & alerts → Create budget**
2. Select billing account for `project-6737f3c2-e011-49b7-ae4`
3. Set name: `LedgerLite Staging`
4. Set budget amount: **$150**
5. Add alert threshold rules:
   - 80% of budget → $120 → email notification
   - 100% of budget → $150 → email notification
6. Under **Manage notifications**, add your email(s)
7. Repeat for Production with a $650 budget

---

## Verify Alert Emails Are Configured

Alert emails go to the billing account contact. To add team emails:

```bash
gcloud billing accounts get-iam-policy $BILLING_ACCOUNT
# Add billing.viewer role to notify additional addresses if needed
```

Or in Console: **Billing → Account management → Add members** with role `Billing Account Viewer`.

---

## After Setup

Once configured, GCP will email automatically when costs cross the 80% and 100% thresholds.
No code changes needed — alerts are entirely managed by GCP Billing.

Record the budget IDs here after creation:

| Budget | ID |
|---|---|
| LedgerLite Staging | _(fill in after `gcloud billing budgets list`)_ |
| LedgerLite Production | _(fill in after `gcloud billing budgets list`)_ |
