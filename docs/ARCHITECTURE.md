# LedgerLite — Architecture

## 1. System Context

```mermaid
graph TB
    subgraph Clients["Client Layer"]
        MOB["📱 Flutter Mobile App\n(Android / iOS)"]
        WEB["🌐 Web Dashboard\n(Next.js — planned)"]
    end

    subgraph Gateway["API Gateway"]
        NGX["nginx Ingress\n(path-based routing)"]
    end

    subgraph Backend["Backend Microservices (FastAPI · Python 3.12)"]
        AUTH["auth-service\n:8001"]
        USER["user-service\n:8002"]
        TXN["transaction-service\n:8003"]
        LEDGER["ledger-service\n:8004"]
        REPORT["report-service\n:8005"]
        AI["ai-service\n:8006"]
        NOTIF["notification-service\n:8007"]
        SYNC["sync-service\n:8008"]
    end

    subgraph Data["Data Layer"]
        PG[("PostgreSQL 16\n(primary store)")]
        REDIS[("Redis 7\n(cache · sessions)")]
    end

    MOB -->|HTTPS / JWT| NGX
    WEB -->|HTTPS / JWT| NGX
    NGX --> AUTH & USER & TXN & LEDGER & REPORT & AI & NOTIF & SYNC
    AUTH & USER & TXN & LEDGER & REPORT & AI & NOTIF & SYNC --> PG
    AUTH & USER & TXN & LEDGER & REPORT & AI & NOTIF & SYNC --> REDIS
```

---

## 2. Microservice Responsibilities

```mermaid
graph LR
    subgraph Auth["Identity"]
        AUTH["auth-service\nRegister · Login\nToken refresh\nJWT HS256"]
    end

    subgraph Profile["User"]
        USER["user-service\nProfile · Onboarding\nSettings · Preferences"]
    end

    subgraph Finance["Finance Core"]
        TXN["transaction-service\nAccounts · Categories\nTransactions\nBalance tracking"]
        LEDGER["ledger-service\nCustomer khata\nDebit / Credit entries\nSettlement"]
        REPORT["report-service\nP&L · Cashflow\nBudget · CSV export"]
    end

    subgraph Intelligence["Intelligence"]
        AI["ai-service\nAuto-categorisation\nSpending insights\nReceipt OCR stub"]
        NOTIF["notification-service\nPayment reminders\nIn-app notifications"]
    end

    subgraph Sync["Offline"]
        SYNC["sync-service\nOffline-first\nConflict resolution\nDelta sync"]
    end

    AUTH -->|JWT validated by| USER & TXN & LEDGER & REPORT & AI & NOTIF & SYNC
    TXN -->|transaction data| REPORT & AI & SYNC
    LEDGER -->|ledger data| NOTIF & SYNC
    USER -->|settings| NOTIF
```

---

## 3. Mobile Offline-First Data Flow

```mermaid
sequenceDiagram
    participant App as Flutter App
    participant SQLite as Local SQLite
    participant Sync as sync-service
    participant DB as PostgreSQL

    App->>SQLite: Write transaction (offline)
    Note over SQLite: Stored with sync_status=pending

    loop Every 5 minutes (background)
        App->>Sync: POST /sync/push {pending_records}
        Sync->>DB: Upsert with conflict resolution
        DB-->>Sync: Accepted / conflicted
        Sync-->>App: {accepted, conflicts}
        App->>SQLite: Mark synced / apply server version

        App->>Sync: GET /sync/pull?since=<last_sync>
        Sync->>DB: Query changes since timestamp
        DB-->>Sync: Delta records
        Sync-->>App: {records}
        App->>SQLite: Merge into local store
    end
```

---

## 4. Authentication Flow

```mermaid
sequenceDiagram
    participant C as Client
    participant A as auth-service
    participant R as Redis
    participant S as Any Service

    C->>A: POST /auth/register {email, password}
    A->>A: bcrypt.hashpw(password)
    A-->>C: 201 {user_id}

    C->>A: POST /auth/login {email, password}
    A->>A: bcrypt.checkpw — verify
    A->>R: Store refresh token (TTL 30d)
    A-->>C: {access_token (15m), refresh_token (30d)}

    C->>S: GET /resource (Bearer access_token)
    S->>S: Decode JWT — get_current_user()
    S-->>C: 200 {data}

    C->>A: POST /auth/refresh {refresh_token}
    A->>R: Validate + rotate token
    A-->>C: {new_access_token, new_refresh_token}
```

---

## 5. Infrastructure Layers

```mermaid
graph TB
    subgraph CI["CI/CD (GitHub Actions)"]
        TEST["test.yml\nper-service pytest\nSQLite in-memory"]
        LINT["lint.yml\nruff check + format"]
        BUILD["build.yml\nDocker → GHCR"]
        DEPLOY["deploy.yml\nmanual trigger\nstaging / prod"]
        TEST --> BUILD
        LINT --> BUILD
        BUILD --> DEPLOY
    end

    subgraph K8s["Kubernetes (Kustomize)"]
        direction LR
        BASE["base/\nnginx · 8 services\npostgres · redis\nmigrations Job"]
        STG["overlays/staging/\nledgerlite-staging ns\n:staging images\n1 replica"]
        PROD["overlays/production/\nledgerlite-production ns\n:production images\n2 replicas"]
        BASE --> STG & PROD
    end

    subgraph DB_layer["Data (persistent)"]
        PG[("PostgreSQL 16\n5Gi PVC")]
        RD[("Redis 7\nAOF persistence")]
    end

    DEPLOY -->|kubectl apply| K8s
    K8s --> DB_layer
```

---

## 6. Database Schema (Core Tables)

```mermaid
erDiagram
    users {
        uuid id PK
        string email UK
        string password_hash
        string full_name
        string phone
        bool is_active
        timestamp created_at
    }
    user_settings {
        uuid id PK
        uuid user_id FK
        string currency
        string language
        jsonb notification_prefs
    }
    accounts {
        uuid id PK
        uuid user_id FK
        string name
        string type
        numeric balance
    }
    transactions {
        uuid id PK
        uuid account_id FK
        uuid category_id FK
        numeric amount
        string type
        string description
        date transaction_date
    }
    categories {
        uuid id PK
        uuid user_id FK
        string name
        string type
    }
    customers {
        uuid id PK
        uuid user_id FK
        string name
        string phone
        numeric balance
    }
    ledger_entries {
        uuid id PK
        uuid customer_id FK
        numeric amount
        string type
        string description
        date due_date
    }

    users ||--o{ user_settings : has
    users ||--o{ accounts : owns
    users ||--o{ categories : defines
    users ||--o{ customers : manages
    accounts ||--o{ transactions : contains
    categories ||--o{ transactions : classifies
    customers ||--o{ ledger_entries : has
```

---

## 7. Security & Role-Based Access Control

### Role model

```
user   — default role, all registered users
         can access: own accounts, transactions, ledger, reports, settings, AI, sync
         cannot access: other users' data, /infra page

admin  — elevated role (is_admin=true OR in ADMIN_EMAILS env var)
         can access: everything user can + /infra costs dashboard
         cannot access: other users' financial data (infra admin ≠ data admin)

── planned (Sprint 14+) ──────────────────────────────────────────────────────
org_owner   — created an organisation; full CRUD + invite/remove members
org_member  — invited to an org; scoped access per owner grant
read_only   — accountant / auditor; read-only on org ledger + reports
```

### Defence-in-depth (admin-only features)

```
Layer 1 — UX        Sidebar nav item hidden (adminOnly flag + isAdmin() check)
Layer 2 — Client    useEffect redirect + useQuery enabled:false for non-admins
Layer 3 — Server    Route handler: reads Bearer token → calls auth-service /auth/me
                    → checks is_admin field OR ADMIN_EMAILS server-only env var
                    → returns 401 (no token) / 403 (not admin)
                    → fails CLOSED on network error or timeout
```

Server layer is the **only real security boundary**. Layers 1–2 are UX.

### Env var split (web-dashboard)

| Variable | Prefix | Purpose |
|---|---|---|
| `ADMIN_EMAILS` | (none — server only) | Real access control. Never in browser. |
| `AUTH_URL` | (none — server only) | Internal K8s auth-service URL. |
| `NEXT_PUBLIC_ADMIN_EMAILS` | `NEXT_PUBLIC_` | UI hint for sidebar/page guards. Not a security control. |

### References

- Developer guide: `docs/developer/rbac-guide.md`
- User personas + permission matrix: `docs/product/user-personas.md`
- Admin runbook: `docs/admin/ADMIN-RUNBOOK.md` (local only — see `docs/admin/README.md`)

---

## 8. Monorepo Layout

```
LedgerLite/
├── apps/
│   ├── mobile-app/          # Flutter (Dart) — 43 files, 5-tab nav
│   └── web-dashboard/       # Next.js (planned)
├── services/
│   ├── auth-service/        # :8001
│   ├── user-service/        # :8002
│   ├── transaction-service/ # :8003
│   ├── ledger-service/      # :8004
│   ├── report-service/      # :8005
│   ├── ai-service/          # :8006
│   ├── notification-service/# :8007
│   └── sync-service/        # :8008
├── database/
│   ├── schema.sql           # canonical schema (source of truth)
│   ├── seeds/               # seed data
│   ├── alembic.ini
│   └── migrations/          # Alembic revisions
├── infrastructure/
│   ├── kubernetes/          # Kustomize base + staging + production
│   └── terraform/           # IaC (planned — Sprint 6C)
├── docs/
│   ├── API.md
│   ├── SPRINT-LOG.md
│   ├── ARCHITECTURE.md      # ← this file
│   └── business/            # planning docs, PRDs, investor materials
├── shared/                  # cross-service reference patterns
├── tests/                   # integration / e2e (future)
├── docker-compose.yml
├── Makefile
├── pyproject.toml           # ruff config
├── ROADMAP.md
├── CLAUDE.md
└── README.md
```
