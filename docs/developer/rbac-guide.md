# LedgerLite — RBAC Developer Guide

**Audience:** Engineers adding features to LedgerLite
**Classification:** Internal — safe to commit
Last updated: 2026-03-14

---

## 1. Role Model

LedgerLite uses a two-tier role model today, with a planned three-tier org model for multi-user support.

### Current roles

| Role | Where stored | Who has it | Grants access to |
|---|---|---|---|
| `user` | Every authenticated JWT | All registered users | Own accounts, transactions, ledger, reports, settings |
| `admin` | `users.is_admin` (DB) or `ADMIN_EMAILS` env var | Founders / ops only | Everything `user` can do + `/infra` page |

### Future roles (planned — Sprint 14+)

| Role | Description | Grants access to |
|---|---|---|
| `org_owner` | Created the organisation | Full CRUD on all org data + invite/remove members |
| `org_member` | Invited to an org | Own data + org-shared data per owner grant |
| `read_only` | Accountant / auditor access | Read-only on ledger, reports, transactions |

**Current implementation:** Only `user` and `admin` are enforced. Org roles are a future database migration (`organisations`, `org_memberships` tables).

---

## 2. Defence-in-Depth Pattern

Every admin-only feature must implement **all three layers** independently. A bypass at one layer must still be blocked by the others.

```
Layer 1 — UX (client)      Sidebar nav item hidden (adminOnly flag)
Layer 2 — Client guard      useEffect redirect + query enabled:false
Layer 3 — Server (API)      Route handler verifies JWT via auth-service; returns 401/403
```

The server layer is the **only real security boundary**. Layers 1 and 2 are UX improvements.

---

## 3. Environment Variables Reference

| Variable | Prefix | Where used | Purpose |
|---|---|---|---|
| `ADMIN_EMAILS` | (none) | Server only — route handlers | Comma-separated admin email allow-list. Never exposed to browser. |
| `AUTH_URL` | (none) | Server only — route handlers | Internal K8s URL for auth-service (`http://auth-service:8000`). Falls back to `NEXT_PUBLIC_AUTH_URL`. |
| `NEXT_PUBLIC_ADMIN_EMAILS` | `NEXT_PUBLIC_` | Browser JS bundle | Same list, used by sidebar / page guards for UX. **Not a security control.** |
| `NEXT_PUBLIC_AUTH_URL` | `NEXT_PUBLIC_` | Browser + server fallback | Public auth-service URL for client-side API calls. |

> **Rule:** Any variable that controls actual access decisions must NOT have the `NEXT_PUBLIC_` prefix. Use `NEXT_PUBLIC_` only for UX hints.

---

## 4. Client-Side Admin Check

Use the `isAdmin()` helper in [lib/auth/is-admin.ts](../../apps/web-dashboard/lib/auth/is-admin.ts) for all client-side role checks:

```typescript
import { isAdmin } from "@/lib/auth/is-admin"

// In a component:
const user = useAuthStore((s) => s.user)
if (!isAdmin(user)) { /* hide or redirect */ }
```

`isAdmin()` checks (in order):
1. `user.is_admin === true` (backend field — populated when backend adds the column)
2. `user.email` in `NEXT_PUBLIC_ADMIN_EMAILS` env var (current mechanism)

Both conditions are checked so the code is forward-compatible: when the backend adds `is_admin`, it takes precedence automatically.

---

## 5. Server-Side Admin Check

Use `resolveAdminStatus()` from [app/api/infra/costs/route.ts](../../apps/web-dashboard/app/api/infra/costs/route.ts) as the reference implementation for any new admin-only API route:

```typescript
async function resolveAdminStatus(token: string): Promise<boolean> {
  const authBase =
    process.env.AUTH_URL ??
    process.env.NEXT_PUBLIC_AUTH_URL ??
    "http://localhost:8001"

  let userEmail: string
  let isAdminFlag: boolean

  try {
    const res = await fetch(`${authBase}/auth/me`, {
      headers: { Authorization: `Bearer ${token}` },
      signal: AbortSignal.timeout(5000),   // ← always set a timeout
    })
    if (!res.ok) return false              // ← auth-service rejected token
    const user = (await res.json()) as { email?: string; is_admin?: boolean }
    if (!user.email) return false
    userEmail = user.email
    isAdminFlag = user.is_admin === true
  } catch {
    return false                           // ← network error — fail CLOSED
  }

  if (isAdminFlag) return true

  const allowList = process.env.ADMIN_EMAILS ?? ""
  if (!allowList) return false

  return allowList
    .split(",")
    .map((e) => e.trim().toLowerCase())
    .includes(userEmail.toLowerCase())
}
```

Key properties of this pattern:
- **Fails closed**: any error (network, timeout, bad response) → deny access
- **5-second timeout**: prevents hanging requests from blocking the response
- **No NEXT_PUBLIC_ env vars**: `ADMIN_EMAILS` stays secret on the server
- **Forward-compatible**: `is_admin` backend field takes precedence when available

---

## 6. Adding a New Admin-Only Feature — Checklist

Follow this checklist every time you add a feature restricted to admins (or any future role).

### 6a. Backend API route (Next.js route handler)

- [ ] Read the Bearer token from `Authorization` header — return `401` if missing
- [ ] Call `resolveAdminStatus(token)` — return `403` if false
- [ ] Never return sensitive data before both checks pass
- [ ] Use `AbortSignal.timeout(5000)` on all auth-service calls

```typescript
export async function GET(request: NextRequest) {
  const authHeader = request.headers.get("authorization")
  if (!authHeader?.startsWith("Bearer ")) {
    return NextResponse.json({ error: "Unauthorized" }, { status: 401 })
  }
  const token = authHeader.slice(7)
  const admin = await resolveAdminStatus(token)
  if (!admin) {
    return NextResponse.json({ error: "Forbidden" }, { status: 403 })
  }
  // ... return data
}
```

### 6b. Page component (client guard)

- [ ] Add `useEffect` redirect for non-admins
- [ ] Add `enabled: isAdmin(user) && !!accessToken` to `useQuery`
- [ ] Return `null` (render nothing) while redirecting
- [ ] Send the access token in the `Authorization` header

```typescript
export default function MyAdminPage() {
  const router   = useRouter()
  const user     = useAuthStore((s) => s.user)
  const token    = useAuthStore((s) => s.accessToken)

  useEffect(() => {
    if (!isAdmin(user)) router.replace("/dashboard")
  }, [user, router])

  const { data, isLoading } = useQuery({
    queryKey: ["my-admin-data", token],
    queryFn: () => fetchMyAdminData(token ?? ""),
    enabled: isAdmin(user) && !!token,
  })

  if (!isAdmin(user)) return null   // prevent flash of content
  // ...
}
```

### 6c. Sidebar navigation

- [ ] Add `adminOnly: true` to the nav item in [components/layout/sidebar.tsx](../../apps/web-dashboard/components/layout/sidebar.tsx)

```typescript
const NAV = [
  // ...
  { href: "/my-admin-feature", label: "My Feature", icon: "★", adminOnly: true },
]
```

### 6d. Fetch helper

- [ ] Pass `token` as a parameter — never read from a global inside the function
- [ ] Set `Authorization: Bearer <token>` header on every request to an admin API route

```typescript
async function fetchMyAdminData(token: string): Promise<MyData> {
  const res = await fetch("/api/my-admin/data", {
    headers: { Authorization: `Bearer ${token}` },
  })
  if (!res.ok) throw new Error("Failed to load data")
  return res.json()
}
```

---

## 7. Adding a New Regular User Feature

Regular user features are simpler — the JWT is validated by each microservice independently via `get_current_user()`. No extra role checks needed.

**Backend (FastAPI):**
```python
@router.get("/resource")
async def get_resource(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    # current_user.id scopes the query — user can only see their own data
    result = await db.execute(
        select(Resource).where(Resource.user_id == current_user.id)
    )
    return result.scalars().all()
```

**Rule:** Always filter database queries by `user_id = current_user.id`. Never return records belonging to other users.

**Web dashboard (Next.js fetch):**
```typescript
async function fetchUserResource(token: string): Promise<Resource[]> {
  const res = await fetch(`${process.env.NEXT_PUBLIC_RESOURCE_URL}/resource`, {
    headers: { Authorization: `Bearer ${token}` },
  })
  if (!res.ok) throw new Error("Failed to load resource")
  return res.json()
}
```

---

## 8. Future: Adding an Org Role Check

When multi-user orgs are implemented (Sprint 14+), the pattern extends as follows.

**Backend — new dependency:**
```python
async def get_org_member(
    current_user: User = Depends(get_current_user),
    org_id: uuid.UUID = Path(...),
    db: AsyncSession = Depends(get_db),
) -> OrgMembership:
    membership = await db.scalar(
        select(OrgMembership).where(
            OrgMembership.org_id == org_id,
            OrgMembership.user_id == current_user.id,
            OrgMembership.is_active == True,
        )
    )
    if not membership:
        raise HTTPException(status_code=403, detail="Not a member of this organisation")
    return membership

@router.get("/org/{org_id}/ledger")
async def get_org_ledger(
    membership: OrgMembership = Depends(get_org_member),
    db: AsyncSession = Depends(get_db),
):
    # membership.role is "owner" | "member" | "read_only"
    ...
```

**Server-side role check helper (to be created):**
```typescript
// Future: resolveOrgRole(token, orgId) → "owner" | "member" | "read_only" | null
```

---

## 9. Security Rules — Non-Negotiable

1. **Never trust the client for access decisions.** Client checks are UX only.
2. **Fail closed.** On any error (network, timeout, missing field) → deny access.
3. **`ADMIN_EMAILS` is never `NEXT_PUBLIC_`.** Keep it server-only.
4. **Always set a timeout** (`AbortSignal.timeout(5000)`) on auth-service calls.
5. **Identical error messages** for 401 and 403 at the response level when caller shouldn't know which is which. (The distinction between "not logged in" vs "not admin" is acceptable to expose here.)
6. **User-scoped queries always.** Regular user routes filter by `user_id` at the database level — no application-layer filtering.
7. **Rotate `JWT_SECRET` immediately** if compromised. See `docs/admin/ADMIN-RUNBOOK.md` (local-only).

---

## 10. References

- [lib/auth/is-admin.ts](../../apps/web-dashboard/lib/auth/is-admin.ts) — `isAdmin()` client helper
- [app/api/infra/costs/route.ts](../../apps/web-dashboard/app/api/infra/costs/route.ts) — reference server-side admin route
- [app/(dashboard)/infra/page.tsx](../../apps/web-dashboard/app/(dashboard)/infra/page.tsx) — reference admin page with guards
- [components/layout/sidebar.tsx](../../apps/web-dashboard/components/layout/sidebar.tsx) — `adminOnly` nav filtering
- [docs/product/user-personas.md](../product/user-personas.md) — user personas and permission matrix
- `docs/admin/ADMIN-RUNBOOK.md` — local-only; see [docs/admin/README.md](../admin/README.md) for access
