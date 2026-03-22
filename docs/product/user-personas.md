# LedgerLite — User Personas & Permission Sets

**Audience:** Product, engineering, design
**Classification:** Internal — safe to commit
Last updated: 2026-03-14

---

## Overview

LedgerLite serves households and small businesses in India and SEA. Users span a wide
range of financial literacy, business complexity, and trust relationships. This document
defines the five core personas, what permissions each holds today, and how the technical
role model maps to real users.

---

## Persona 1 — Solo Entrepreneur

**Who:** A self-employed trader, freelancer, or micro-business owner managing their own
accounts. The most common LedgerLite user.

**Goals:**
- Track income and expenses across one or more accounts
- Manage customer khata (credit/debit with clients)
- Generate simple P&L and cashflow reports
- Log transactions offline (poor connectivity)

**Technical role:** `user`

**Permissions today:**

| Feature | Access |
|---|---|
| Register / login | Full |
| Own accounts (create, view, edit) | Full |
| Own transactions (create, view, edit, soft-delete) | Full |
| Own categories (create, view, edit) | Full |
| Own customers + ledger entries | Full |
| Reports (P&L, cashflow, budget, CSV export) | Own data only |
| AI auto-categorisation | Own transactions only |
| Payment reminders (send / receive) | Own ledger only |
| Offline sync | Own data only |
| Other users' data | None |
| Infra costs dashboard | None |

**Org permissions (Sprint 14 — live):**
- Automatically gets a personal org on registration (`owner` role)
- Can create additional organisations and invite staff (`owner` role)

---

## Persona 2 — Household Manager

**Who:** An individual managing shared household finances — groceries, rent, utilities,
family savings goals.

**Goals:**
- Track shared family expenses categorised by type
- Set and monitor budgets
- Quick transaction entry (mobile-first)

**Technical role:** `user`

**Permissions today:** Same as Persona 1 — full access to their own data, nothing else.

**Differences from Persona 1:**
- Typically uses expense/income categories differently (household-specific)
- Less likely to use ledger (customer khata) feature
- More likely to use budget alerts and reports

**Org permissions (Sprint 14 — live):**
- Shared household account is now supported via org invitation (`member` role)

---

## Persona 3 — Business Owner with Staff

**Who:** A shop owner, small manufacturer, or service business with 2–10 employees who
need to enter transactions (sales staff, cashiers).

**Goals:**
- Multiple staff can enter transactions during the day
- Owner reviews, edits, and approves entries
- Owner has full reporting visibility
- Staff cannot see reports or delete records

**Technical roles (Sprint 14 — live):**

| Team member | Role | What they can do |
|---|---|---|
| Business owner | `owner` | Full CRUD + reports + invite/remove/role-change members |
| Cashier / sales staff | `member` | Full CRUD on org data (cannot manage members) |
| Accountant (external) | `read_only` | Read-only on all org data — no writes |

Active org selected via `X-Org-ID` HTTP header; falls back to personal org if absent.

---

## Persona 4 — Accountant / Bookkeeper

**Who:** An external accountant hired by a business owner (Persona 3) to review books,
reconcile accounts, and generate reports for tax filing.

**Goals:**
- Read-only access to all financial data for an organisation
- Export CSV / PDF reports
- No ability to create, modify, or delete records

**Technical role (Sprint 14 — live):** `read_only` — invited to the business owner's org with `role = "read_only"` via `POST /organisations/{org_id}/members`.

**Permissions (read_only role):**

| Feature | Access |
|---|---|
| View accounts | Read |
| View all transactions | Read |
| View ledger entries | Read |
| Export reports (CSV, PDF) | Full |
| Create / edit any records | None |
| Invite / remove users | None |
| Infra costs | None |

---

## Persona 5 — Platform Administrator

**Who:** Founders and ops engineers at LedgerLite. Responsible for infrastructure,
user support, deployments, and security.

**Goals:**
- View live infrastructure costs (GKE, Cloud SQL, Redis, etc.)
- Monitor GCP budget against caps
- Deploy new service versions
- Rotate secrets and revoke compromised sessions

**Technical role:** `admin` (via `users.is_admin = true` or `ADMIN_EMAILS` env var)

**Permissions today:**

| Feature | Access |
|---|---|
| Everything a `user` can do | Full |
| `/infra` page (Infra Costs dashboard) | Full |
| View cost breakdown by resource | Full |
| View sprint-exit cost snapshots | Full |
| View budget status (staging + production) | Full |
| Rotate JWT secret | Via `docs/admin/ADMIN-RUNBOOK.md` (local only) |
| Access GCP project / GKE cluster | Via `gcloud` CLI (IAM-controlled) |
| Deploy to staging / production | Via GitHub Actions `deploy.yml` (manual trigger) |
| Access other users' financial data | None (platform admin ≠ data admin) |

> **Security note:** Platform admins do NOT have direct read access to user financial data
> through the application. Admin elevation only grants infrastructure visibility.
> Any access to user data requires a separate, auditable path (e.g., direct DB query
> with logging, reviewed by lead engineer).

**How admin is granted today:**
1. Add email to `ADMIN_EMAILS` (server-side K8s env) and `NEXT_PUBLIC_ADMIN_EMAILS` (client-side)
2. Redeploy `web-dashboard` pod
3. Full procedure: see `docs/admin/ADMIN-RUNBOOK.md` → Section 1

---

## Permission Matrix (Current)

| Feature | Persona 1–2 (`user`) | Persona 3–4 (org roles — Sprint 14) | Persona 5 (`admin`) |
|---|---|---|---|
| Register / login | ✅ | ✅ | ✅ |
| Own accounts | ✅ CRUD | ✅ (scoped by role) | ✅ |
| Own transactions | ✅ CRUD | ✅ (scoped by role) | ✅ |
| Own categories | ✅ CRUD | ✅ | ✅ |
| Own ledger / customers | ✅ CRUD | ✅ (scoped by role) | ✅ |
| Reports | ✅ own only | ✅ scoped | ✅ |
| AI features | ✅ own only | ✅ own only | ✅ |
| Notifications | ✅ own only | ✅ own only | ✅ |
| Offline sync | ✅ | ✅ | ✅ |
| Other user's data | ❌ | ❌ | ❌ |
| `/infra` page | ❌ | ❌ | ✅ |
| Deploy / rotate secrets | ❌ | ❌ | ✅ (via ops tooling) |

---

## Technical Role Roadmap

```
Sprint 13 (done)
  └── admin role: is_admin field + ADMIN_EMAILS env var
      Used for: /infra costs dashboard

Sprint 14 (done — PR #18)
  └── org model: organisations + org_memberships tables (migrations 004 + 005)
      Roles: owner, member, read_only
      Used for: multi-user business accounts, accountant access
      Transport: X-Org-ID header (fallback: personal org)

Sprint 16+ (future)
  └── granular permissions: org-level feature flags
      E.g., "cashier can create but not delete transactions"
```

---

## Principles

1. **Least privilege.** Every user starts as `user` — no elevated access by default.
2. **Data isolation.** Users never see other users' data unless explicitly granted via an org membership.
3. **Infrastructure ≠ data.** Platform admin access (`admin` role) does not grant access to user financial data.
4. **Fail closed.** Missing role or network error → deny access, never default to allow.
5. **Audit trail.** All admin actions should be traceable. Org membership changes log to an `audit_log` table (future).

---

## References

- [docs/developer/rbac-guide.md](../developer/rbac-guide.md) — technical implementation guide for engineers
- `docs/admin/ADMIN-RUNBOOK.md` — local-only; see [docs/admin/README.md](../admin/README.md) for access
- [apps/web-dashboard/lib/auth/is-admin.ts](../../apps/web-dashboard/lib/auth/is-admin.ts) — client-side admin check
- [apps/web-dashboard/app/api/infra/costs/route.ts](../../apps/web-dashboard/app/api/infra/costs/route.ts) — server-side admin enforcement
