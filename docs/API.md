# LedgerLite API Documentation

## Base URLs

| Service              | Port | Base URL                  |
|----------------------|------|---------------------------|
| Auth Service         | 8001 | `http://localhost:8001`   |
| User Service         | 8002 | `http://localhost:8002`   |
| Transaction Service  | 8003 | `http://localhost:8003`   |
| Ledger Service       | 8004 | `http://localhost:8004`   |
| Report Service       | 8005 | `http://localhost:8005`   |
| Notification Service | 8007 | `http://localhost:8007`   |

## Authentication

All endpoints except the following require a Bearer token in the `Authorization` header:

- `POST /auth/register`
- `POST /auth/login`
- `POST /auth/refresh`
- `GET /health`

To authenticate, include the `access_token` received from the login response:

```
Authorization: Bearer <access_token>
```

Tokens are JWTs with a `type` claim (`access` or `refresh`). Access tokens are short-lived; use the refresh endpoint to obtain a new pair before expiry. Refresh tokens are single-use -- once used, the old token is invalidated.

---

## Auth Service (port 8001)

### POST /auth/register

Register a new user account.

**Request Body:**

```json
{
  "email": "user@example.com",
  "password": "securepassword",
  "full_name": "Jane Doe",
  "phone": "+919876543210"
}
```

| Field     | Type   | Required | Notes              |
|-----------|--------|----------|--------------------|
| email     | string | Yes      | Must be valid email |
| password  | string | Yes      | Minimum 8 characters |
| full_name | string | Yes      |                    |
| phone     | string | No       |                    |

**Response:** `201 Created`

```json
{
  "id": "uuid",
  "email": "user@example.com",
  "full_name": "Jane Doe",
  "phone": "+919876543210",
  "is_active": true,
  "created_at": "2026-01-15T10:30:00Z",
  "updated_at": "2026-01-15T10:30:00Z"
}
```

**curl example:**

```bash
curl -X POST http://localhost:8001/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "securepassword",
    "full_name": "Jane Doe",
    "phone": "+919876543210"
  }'
```

---

### POST /auth/login

Authenticate and receive access and refresh tokens.

**Request Body:**

```json
{
  "email": "user@example.com",
  "password": "securepassword"
}
```

| Field    | Type   | Required |
|----------|--------|----------|
| email    | string | Yes      |
| password | string | Yes      |

**Response:** `200 OK`

```json
{
  "access_token": "eyJhbGciOi...",
  "refresh_token": "eyJhbGciOi...",
  "token_type": "bearer"
}
```

**curl example:**

```bash
curl -X POST http://localhost:8001/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "securepassword"
  }'
```

---

### GET /auth/me

Retrieve the currently authenticated user's profile.

**Headers:** `Authorization: Bearer <access_token>`

**Response:** `200 OK`

```json
{
  "id": "uuid",
  "email": "user@example.com",
  "full_name": "Jane Doe",
  "phone": "+919876543210",
  "is_active": true,
  "created_at": "2026-01-15T10:30:00Z",
  "updated_at": "2026-01-15T10:30:00Z"
}
```

---

### POST /auth/refresh

Exchange a valid refresh token for a new access/refresh token pair. The old refresh token is invalidated immediately (single-use rotation).

**Request Body:**

```json
{
  "refresh_token": "eyJhbGciOi..."
}
```

**Response:** `200 OK`

```json
{
  "access_token": "eyJhbGciOi...",
  "refresh_token": "eyJhbGciOi...",
  "token_type": "bearer"
}
```

---

### GET /health

Health check endpoint. No authentication required.

**Response:** `200 OK`

```json
{
  "status": "ok",
  "service": "auth"
}
```

---

## User Service (port 8002)

All endpoints below require `Authorization: Bearer <access_token>` unless noted otherwise.

### GET /users/me

Retrieve the current user's profile including settings.

**Response:** `200 OK`

```json
{
  "id": "uuid",
  "email": "user@example.com",
  "full_name": "Jane Doe",
  "phone": "+919876543210",
  "is_active": true,
  "created_at": "2026-01-15T10:30:00Z",
  "updated_at": "2026-01-15T10:30:00Z",
  "settings": {
    "account_type": "personal",
    "currency": "INR",
    "language": "en",
    "business_category": null,
    "notifications_enabled": true,
    "onboarding_completed": true
  }
}
```

---

### PUT /users/me

Update the current user's profile fields.

**Request Body:**

```json
{
  "full_name": "Jane Smith",
  "phone": "+919876500000",
  "email": "jane.smith@example.com"
}
```

| Field     | Type   | Required | Notes                    |
|-----------|--------|----------|--------------------------|
| full_name | string | No       | Updated display name     |
| phone     | string | No       | Updated phone number     |
| email     | string | No       | Updated email address    |

**Response:** `200 OK` -- Returns the updated UserProfile.

---

### POST /users/me/onboarding

Complete the onboarding flow. This endpoint can only be called once per user.

**Request Body:**

```json
{
  "account_type": "personal",
  "currency": "INR",
  "language": "en",
  "business_category": "retail"
}
```

| Field             | Type   | Required | Notes                                    |
|-------------------|--------|----------|------------------------------------------|
| account_type      | string | Yes      | One of: `personal`, `business`, `both`   |
| currency          | string | Yes      | e.g., `INR`, `USD`, `SGD`               |
| language          | string | Yes      | e.g., `en`, `hi`, `ta`                  |
| business_category | string | No       | Relevant for business or both accounts   |

**Response:** `200 OK`

**Error:** `409 Conflict` if onboarding has already been completed.

---

### PUT /users/me/settings

Update user settings.

**Request Body:**

```json
{
  "notifications_enabled": false,
  "language": "hi",
  "currency": "USD"
}
```

| Field                 | Type    | Required | Notes                        |
|-----------------------|---------|----------|------------------------------|
| notifications_enabled | boolean | No       | Enable/disable notifications |
| language              | string  | No       | Display language             |
| currency              | string  | No       | Default currency             |

**Response:** `200 OK` -- Returns the updated settings.

---

### DELETE /users/me

Deactivate the current user's account. This is a soft delete; the user record is retained but marked inactive.

**Response:** `200 OK`

---

### GET /health

Health check endpoint. No authentication required.

**Response:** `200 OK`

```json
{
  "status": "ok",
  "service": "user"
}
```

---

## Transaction Service (port 8003)

All endpoints require `Authorization: Bearer <access_token>`.

### Accounts

#### POST /accounts

Create a new financial account.

**Request Body:**

```json
{
  "name": "Savings Account",
  "type": "bank",
  "currency": "INR"
}
```

| Field    | Type   | Required | Notes                                          |
|----------|--------|----------|-------------------------------------------------|
| name     | string | Yes      | Account display name                            |
| type     | string | Yes      | One of: `cash`, `bank`, `credit_card`, `wallet`, `loan` |
| currency | string | No       | 3-letter ISO code, defaults to `INR`            |

**Response:** `201 Created`

```json
{
  "id": "uuid",
  "user_id": "uuid",
  "name": "Savings Account",
  "type": "bank",
  "currency": "INR",
  "balance": "0.00",
  "is_active": true,
  "created_at": "2026-02-18T10:00:00Z",
  "updated_at": "2026-02-18T10:00:00Z"
}
```

---

#### GET /accounts

List all active accounts for the current user.

**Response:** `200 OK` -- Array of AccountResponse objects.

---

#### GET /accounts/{id}

Get a single account by ID.

**Response:** `200 OK` or `404 Not Found`

---

#### PUT /accounts/{id}

Update an account's name or type.

**Request Body:**

```json
{
  "name": "New Name",
  "type": "wallet"
}
```

**Response:** `200 OK`

---

#### DELETE /accounts/{id}

Deactivate an account (soft delete).

**Response:** `200 OK`

---

### Categories

#### POST /categories

Create a custom category.

**Request Body:**

```json
{
  "name": "Groceries",
  "type": "expense",
  "icon": "cart"
}
```

| Field | Type   | Required | Notes                             |
|-------|--------|----------|-----------------------------------|
| name  | string | Yes      | Category display name             |
| type  | string | Yes      | One of: `income`, `expense`       |
| icon  | string | No       | Icon identifier for mobile UI     |

**Response:** `201 Created`

---

#### GET /categories

List all categories available to the user (system categories + user's custom categories).

**Query Parameters:**

| Param | Type   | Required | Notes                               |
|-------|--------|----------|--------------------------------------|
| type  | string | No       | Filter by `income` or `expense`     |

**Response:** `200 OK` -- Array of CategoryResponse objects.

---

### Transactions

#### POST /transactions

Create a new transaction. Automatically updates the account balance.

**Request Body:**

```json
{
  "account_id": "uuid",
  "category_id": "uuid",
  "type": "expense",
  "amount": "150.00",
  "description": "Grocery shopping",
  "transaction_date": "2026-02-18T14:30:00Z"
}
```

| Field            | Type     | Required | Notes                                    |
|------------------|----------|----------|------------------------------------------|
| account_id       | uuid     | Yes      | Must belong to the current user          |
| category_id      | uuid     | No       | Optional category tag                    |
| type             | string   | Yes      | One of: `income`, `expense`, `transfer`  |
| amount           | decimal  | Yes      | Must be positive                         |
| description      | string   | No       | Free-text note                           |
| transaction_date | datetime | Yes      | ISO 8601 format                          |

**Response:** `201 Created`

**Balance effect:** `income` adds to account balance, `expense` subtracts.

---

#### GET /transactions

List transactions with filtering and pagination.

**Query Parameters:**

| Param       | Type     | Required | Notes                          |
|-------------|----------|----------|--------------------------------|
| account_id  | uuid     | No       | Filter by account              |
| category_id | uuid     | No       | Filter by category             |
| type        | string   | No       | Filter by income/expense/transfer |
| date_from   | datetime | No       | Start of date range            |
| date_to     | datetime | No       | End of date range              |
| skip        | int      | No       | Offset (default: 0)            |
| limit       | int      | No       | Page size (default: 20, max: 100) |

**Response:** `200 OK`

```json
{
  "items": [
    {
      "id": "uuid",
      "user_id": "uuid",
      "account_id": "uuid",
      "category_id": "uuid",
      "type": "expense",
      "amount": "150.00",
      "description": "Grocery shopping",
      "transaction_date": "2026-02-18T14:30:00Z",
      "created_at": "2026-02-18T14:30:00Z",
      "updated_at": "2026-02-18T14:30:00Z"
    }
  ],
  "total": 42,
  "skip": 0,
  "limit": 20
}
```

---

#### GET /transactions/{id}

Get a single transaction by ID.

**Response:** `200 OK` or `404 Not Found`

---

#### PUT /transactions/{id}

Update a transaction. The account balance is recalculated (old impact reversed, new impact applied).

**Request Body:**

```json
{
  "amount": "200.00",
  "description": "Updated description",
  "type": "expense"
}
```

All fields are optional.

**Response:** `200 OK`

---

#### DELETE /transactions/{id}

Delete a transaction. The balance impact is reversed on the associated account.

**Response:** `200 OK`

---

## Ledger Service (port 8004)

All endpoints require `Authorization: Bearer <access_token>`.

### Customers

#### POST /customers

Create a new customer for credit tracking.

**Request Body:**

```json
{
  "name": "Rahul Sharma",
  "phone": "+919876543210",
  "email": "rahul@example.com",
  "address": "123 Main St, Mumbai"
}
```

| Field   | Type   | Required | Notes                        |
|---------|--------|----------|------------------------------|
| name    | string | Yes      | Customer display name        |
| phone   | string | No       | Customer phone number        |
| email   | string | No       | Customer email address       |
| address | string | No       | Customer address             |

**Response:** `201 Created`

```json
{
  "id": "uuid",
  "user_id": "uuid",
  "name": "Rahul Sharma",
  "phone": "+919876543210",
  "email": "rahul@example.com",
  "address": "123 Main St, Mumbai",
  "created_at": "2026-02-18T10:00:00Z",
  "updated_at": "2026-02-18T10:00:00Z"
}
```

---

#### GET /customers

List all customers for the current user with search and outstanding balance.

**Query Parameters:**

| Param  | Type   | Required | Notes                                           |
|--------|--------|----------|-------------------------------------------------|
| search | string | No       | Search across name, phone, and email (case-insensitive) |
| skip   | int    | No       | Offset (default: 0)                             |
| limit  | int    | No       | Page size (default: 20, max: 100)               |

**Response:** `200 OK`

```json
{
  "items": [
    {
      "id": "uuid",
      "user_id": "uuid",
      "name": "Rahul Sharma",
      "phone": "+919876543210",
      "email": "rahul@example.com",
      "address": "123 Main St, Mumbai",
      "created_at": "2026-02-18T10:00:00Z",
      "updated_at": "2026-02-18T10:00:00Z",
      "outstanding_balance": "1500.00"
    }
  ],
  "total": 10,
  "skip": 0,
  "limit": 20
}
```

---

#### GET /customers/{id}

Get a single customer by ID with credit summary.

**Response:** `200 OK`

```json
{
  "id": "uuid",
  "user_id": "uuid",
  "name": "Rahul Sharma",
  "phone": "+919876543210",
  "email": "rahul@example.com",
  "address": "123 Main St, Mumbai",
  "created_at": "2026-02-18T10:00:00Z",
  "updated_at": "2026-02-18T10:00:00Z",
  "outstanding_balance": "1500.00"
}
```

**Error:** `404 Not Found` if customer does not exist or does not belong to the current user.

---

#### PUT /customers/{id}

Update a customer's information.

**Request Body:**

```json
{
  "name": "Rahul K. Sharma",
  "phone": "+919876500000",
  "email": "rahul.k@example.com",
  "address": "456 New St, Mumbai"
}
```

All fields are optional.

**Response:** `200 OK` -- Returns the updated CustomerResponse.

---

### Ledger Entries

#### POST /ledger-entry

Create a new ledger entry (debit or credit) for a customer.

**Request Body:**

```json
{
  "customer_id": "uuid",
  "amount": "1500.00",
  "type": "debit",
  "due_date": "2026-03-01T00:00:00Z",
  "description": "Goods purchased on credit"
}
```

| Field       | Type     | Required | Notes                                  |
|-------------|----------|----------|----------------------------------------|
| customer_id | uuid     | Yes      | Must belong to the current user        |
| amount      | decimal  | Yes      | Must be positive                       |
| type        | string   | Yes      | One of: `debit`, `credit`              |
| due_date    | datetime | No       | Expected payment date (ISO 8601)       |
| description | string   | No       | Free-text note                         |

**Response:** `201 Created`

```json
{
  "id": "uuid",
  "customer_id": "uuid",
  "user_id": "uuid",
  "amount": "1500.00",
  "type": "debit",
  "due_date": "2026-03-01T00:00:00Z",
  "description": "Goods purchased on credit",
  "is_settled": false,
  "created_at": "2026-02-18T10:00:00Z",
  "updated_at": "2026-02-18T10:00:00Z"
}
```

**Balance effect:** `debit` increases outstanding balance, `credit` decreases it. Only unsettled entries are included in outstanding balance calculations.

---

#### GET /ledger/{customer_id}

Get the full credit history for a customer with balance summary.

**Query Parameters:**

| Param | Type | Required | Notes                            |
|-------|------|----------|----------------------------------|
| skip  | int  | No       | Offset (default: 0)             |
| limit | int  | No       | Page size (default: 20, max: 100) |

**Response:** `200 OK`

```json
{
  "customer_id": "uuid",
  "total_debit": "5000.00",
  "total_credit": "3500.00",
  "outstanding_balance": "1500.00",
  "entries": [
    {
      "id": "uuid",
      "customer_id": "uuid",
      "user_id": "uuid",
      "amount": "1500.00",
      "type": "debit",
      "due_date": "2026-03-01T00:00:00Z",
      "description": "Goods purchased on credit",
      "is_settled": false,
      "created_at": "2026-02-18T10:00:00Z",
      "updated_at": "2026-02-18T10:00:00Z"
    }
  ],
  "total": 15,
  "skip": 0,
  "limit": 20
}
```

---

#### PUT /ledger-entry/{id}

Mark a ledger entry as settled or record a partial payment.

**Request Body:**

```json
{
  "is_settled": true
}
```

| Field      | Type    | Required | Notes                                    |
|------------|---------|----------|------------------------------------------|
| is_settled | boolean | No       | Mark the entry as fully settled          |
| amount     | decimal | No       | Update amount (for partial payment)      |

**Response:** `200 OK` -- Returns the updated LedgerEntryResponse.

---

### GET /health

Health check endpoint. No authentication required.

**Response:** `200 OK`

```json
{
  "status": "ok",
  "service": "ledger"
}
```

---

## Report Service (port 8005)

All endpoints require `Authorization: Bearer <access_token>`.

### GET /reports/profit-loss

Get profit and loss report for a date range: total income, total expenses, net profit, with category breakdowns.

**Query Parameters:**

| Param      | Type | Required | Notes                          |
|------------|------|----------|--------------------------------|
| start_date | date | No       | Start of range (default: 1st of current month) |
| end_date   | date | No       | End of range (default: today)  |

**Response:** `200 OK`

```json
{
  "start_date": "2026-01-01",
  "end_date": "2026-01-31",
  "total_income": "60000.00",
  "total_expenses": "16500.00",
  "net_profit": "43500.00",
  "income_by_category": [
    {"category_id": "uuid", "category_name": "Salary", "total": "50000.00"}
  ],
  "expense_by_category": [
    {"category_id": "uuid", "category_name": "Rent", "total": "12000.00"}
  ]
}
```

---

### GET /reports/cashflow

Get cashflow report grouped by time period.

**Query Parameters:**

| Param      | Type   | Required | Notes                                    |
|------------|--------|----------|------------------------------------------|
| start_date | date   | No       | Start of range (default: 1st of month)   |
| end_date   | date   | No       | End of range (default: today)            |
| period     | string | No       | One of: `daily`, `weekly`, `monthly` (default: `monthly`) |

**Response:** `200 OK`

```json
{
  "start_date": "2026-01-01",
  "end_date": "2026-02-28",
  "period": "monthly",
  "periods": [
    {"period": "2026-01", "inflows": "60000.00", "outflows": "16500.00", "net": "43500.00"},
    {"period": "2026-02", "inflows": "50000.00", "outflows": "2500.00", "net": "47500.00"}
  ],
  "total_inflows": "110000.00",
  "total_outflows": "19000.00",
  "net_cashflow": "91000.00"
}
```

---

### GET /reports/budget

Get spending breakdown by expense category for a date range.

**Query Parameters:**

| Param      | Type | Required | Notes                          |
|------------|------|----------|--------------------------------|
| start_date | date | No       | Start of range (default: 1st of month) |
| end_date   | date | No       | End of range (default: today)  |

**Response:** `200 OK`

```json
{
  "start_date": "2026-01-01",
  "end_date": "2026-01-31",
  "categories": [
    {"category_id": "uuid", "category_name": "Rent", "spent": "12000.00", "transaction_count": 1},
    {"category_id": "uuid", "category_name": "Food", "spent": "3000.00", "transaction_count": 1}
  ],
  "total_spent": "16500.00"
}
```

---

### GET /reports/summary

Get a dashboard summary: account balances, income/expense totals, top categories, outstanding ledger amounts.

**Response:** `200 OK`

```json
{
  "total_balance": "20000.00",
  "total_income": "110000.00",
  "total_expenses": "19000.00",
  "net_profit": "91000.00",
  "transaction_count": 7,
  "account_count": 2,
  "top_expense_categories": [
    {"category_name": "Rent", "total": "12000.00"}
  ],
  "top_income_categories": [
    {"category_name": "Salary", "total": "100000.00"}
  ],
  "outstanding_receivables": "5000.00",
  "outstanding_payables": "2000.00"
}
```

---

### GET /reports/export

Export transactions as CSV for a date range.

**Query Parameters:**

| Param      | Type   | Required | Notes                          |
|------------|--------|----------|--------------------------------|
| start_date | date   | No       | Start of range                 |
| end_date   | date   | No       | End of range                   |
| format     | string | No       | Currently only `csv` (default) |

**Response:** `200 OK`

```json
{
  "format": "csv",
  "filename": "transactions_2026-01-01_2026-01-31.csv",
  "content_type": "text/csv",
  "data": "ID,Date,Type,Amount,Category,Account,Description\n..."
}
```

---

### GET /health

Health check endpoint. No authentication required.

**Response:** `200 OK`

```json
{
  "status": "ok",
  "service": "report"
}
```

---

## Notification Service (port 8007)

All endpoints require `Authorization: Bearer <access_token>`.

### GET /notifications

List the current user's notifications with pagination.

**Query Parameters:**

| Param       | Type    | Required | Notes                            |
|-------------|---------|----------|----------------------------------|
| skip        | int     | No       | Offset (default: 0)             |
| limit       | int     | No       | Page size (default: 20, max: 100) |
| unread_only | boolean | No       | Filter to unread only (default: false) |

**Response:** `200 OK`

```json
{
  "items": [
    {
      "id": "uuid",
      "user_id": "uuid",
      "type": "reminder",
      "title": "Payment reminder for Rahul",
      "message": "Reminder: Rahul has an outstanding balance of 3000.00.",
      "is_read": false,
      "related_entity_id": "uuid",
      "created_at": "2026-02-18T10:00:00Z"
    }
  ],
  "total": 5,
  "skip": 0,
  "limit": 20,
  "unread_count": 3
}
```

---

### PUT /notifications/{id}/read

Mark a notification as read.

**Response:** `200 OK`

```json
{
  "id": "uuid",
  "is_read": true
}
```

**Error:** `404 Not Found` if notification does not exist or does not belong to the current user.

---

### POST /notifications/reminder

Trigger a credit reminder notification for a customer with outstanding balance.

**Request Body:**

```json
{
  "customer_id": "uuid",
  "message": "Please pay your outstanding balance"
}
```

| Field       | Type   | Required | Notes                                |
|-------------|--------|----------|--------------------------------------|
| customer_id | uuid   | Yes      | Must belong to the current user      |
| message     | string | No       | Custom message (auto-generated if omitted) |

**Response:** `201 Created`

```json
{
  "id": "uuid",
  "user_id": "uuid",
  "type": "reminder",
  "title": "Payment reminder for Rahul",
  "message": "Reminder: Rahul has an outstanding balance of 3000.00.",
  "is_read": false,
  "related_entity_id": "uuid",
  "created_at": "2026-02-18T10:00:00Z"
}
```

**Error:** `404 Not Found` if customer does not exist. `400 Bad Request` if customer has no outstanding balance.

---

### GET /health

Health check endpoint. No authentication required.

**Response:** `200 OK`

```json
{
  "status": "ok",
  "service": "notification"
}
```

---

## Error Responses

All services return errors in a consistent format. Common status codes:

| Status Code | Meaning              | Description                                                                 |
|-------------|----------------------|-----------------------------------------------------------------------------|
| 401         | Unauthorized         | Missing, invalid, or expired Bearer token. Re-authenticate or refresh.     |
| 404         | Not Found            | The requested resource does not exist.                                      |
| 409         | Conflict             | The request conflicts with existing state (e.g., duplicate email, onboarding already completed). |
| 422         | Validation Error     | The request body failed validation (missing required fields, invalid types, password too short). |

Error response body example:

```json
{
  "detail": "A description of what went wrong"
}
```

For 422 validation errors, the response includes field-level detail:

```json
{
  "detail": [
    {
      "loc": ["body", "password"],
      "msg": "ensure this has at least 8 characters",
      "type": "value_error"
    }
  ]
}
```

---

## Data Types

### UserProfile

```json
{
  "id": "uuid",
  "email": "string",
  "full_name": "string",
  "phone": "string | null",
  "is_active": "boolean",
  "created_at": "datetime (ISO 8601)",
  "updated_at": "datetime (ISO 8601)",
  "settings": "UserSettings | null"
}
```

The `settings` field is included when fetched through the User Service and is `null` if onboarding has not been completed.

### TokenResponse

```json
{
  "access_token": "string (JWT)",
  "refresh_token": "string (JWT)",
  "token_type": "bearer"
}
```

### UserSettings

```json
{
  "account_type": "personal | business | both",
  "currency": "string (e.g., INR, USD)",
  "language": "string (e.g., en, hi)",
  "business_category": "string | null",
  "notifications_enabled": "boolean",
  "onboarding_completed": "boolean"
}
```

### AccountResponse

```json
{
  "id": "uuid",
  "user_id": "uuid",
  "name": "string",
  "type": "cash | bank | credit_card | wallet | loan",
  "currency": "string (e.g., INR)",
  "balance": "decimal (string representation)",
  "is_active": "boolean",
  "created_at": "datetime (ISO 8601)",
  "updated_at": "datetime (ISO 8601)"
}
```

### CategoryResponse

```json
{
  "id": "uuid",
  "user_id": "uuid | null",
  "name": "string",
  "type": "income | expense",
  "icon": "string | null",
  "is_system": "boolean",
  "created_at": "datetime (ISO 8601)"
}
```

### TransactionResponse

```json
{
  "id": "uuid",
  "user_id": "uuid",
  "account_id": "uuid",
  "category_id": "uuid | null",
  "type": "income | expense | transfer",
  "amount": "decimal (string representation)",
  "description": "string | null",
  "transaction_date": "datetime (ISO 8601)",
  "created_at": "datetime (ISO 8601)",
  "updated_at": "datetime (ISO 8601)"
}
```

### TransactionListResponse

```json
{
  "items": "TransactionResponse[]",
  "total": "integer",
  "skip": "integer",
  "limit": "integer"
}
```

### CustomerResponse

```json
{
  "id": "uuid",
  "user_id": "uuid",
  "name": "string",
  "phone": "string | null",
  "email": "string | null",
  "address": "string | null",
  "created_at": "datetime (ISO 8601)",
  "updated_at": "datetime (ISO 8601)"
}
```

### CustomerWithBalance

Extends CustomerResponse with the outstanding balance field.

```json
{
  "id": "uuid",
  "user_id": "uuid",
  "name": "string",
  "phone": "string | null",
  "email": "string | null",
  "address": "string | null",
  "created_at": "datetime (ISO 8601)",
  "updated_at": "datetime (ISO 8601)",
  "outstanding_balance": "decimal (string representation)"
}
```

The `outstanding_balance` is calculated as the sum of unsettled debit entries minus the sum of unsettled credit entries for the customer.

### CustomerListResponse

```json
{
  "items": "CustomerWithBalance[]",
  "total": "integer",
  "skip": "integer",
  "limit": "integer"
}
```

### LedgerEntryResponse

```json
{
  "id": "uuid",
  "customer_id": "uuid",
  "user_id": "uuid",
  "amount": "decimal (string representation)",
  "type": "debit | credit",
  "due_date": "datetime (ISO 8601) | null",
  "description": "string | null",
  "is_settled": "boolean",
  "created_at": "datetime (ISO 8601)",
  "updated_at": "datetime (ISO 8601)"
}
```

### LedgerSummary

Returned by `GET /ledger/{customer_id}`, wraps the ledger entry list with balance aggregation.

```json
{
  "customer_id": "uuid",
  "total_debit": "decimal (string representation)",
  "total_credit": "decimal (string representation)",
  "outstanding_balance": "decimal (string representation)",
  "entries": "LedgerEntryResponse[]",
  "total": "integer",
  "skip": "integer",
  "limit": "integer"
}
```

### NotificationResponse

```json
{
  "id": "uuid",
  "user_id": "uuid",
  "type": "reminder | payment | overdue | system",
  "title": "string",
  "message": "string",
  "is_read": "boolean",
  "related_entity_id": "uuid | null",
  "created_at": "datetime (ISO 8601)"
}
```

### NotificationListResponse

```json
{
  "items": "NotificationResponse[]",
  "total": "integer",
  "skip": "integer",
  "limit": "integer",
  "unread_count": "integer"
}
```
