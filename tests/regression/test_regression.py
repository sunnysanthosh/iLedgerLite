"""
Regression Tests — cross-service data integrity checks with seeded data.

Runs in-process using ASGI test clients with SQLite + seed data.
Run with: cd C:/Temp/LedgerLite && pytest tests/regression/ -v
"""

from decimal import Decimal

from shared.test_data import ACCOUNT_RAJESH_BIZ_CASH_ID, CAT_SALARY_ID


# ===========================================================================
# User Isolation
# ===========================================================================
class TestUserIsolation:
    """Verify users can only see their own data."""

    async def test_priya_sees_only_her_accounts(self, seeded_txn_client, priya_headers):
        """Priya's account list should only contain her accounts."""
        resp = await seeded_txn_client.get("/accounts", headers=priya_headers)
        assert resp.status_code == 200
        data = resp.json()
        items = data.get("items", data) if isinstance(data, dict) else data
        assert isinstance(items, list)
        assert len(items) == 3  # Cash, SBI, HDFC CC

    async def test_rajesh_sees_only_his_accounts(self, seeded_txn_client, rajesh_headers):
        """Rajesh's account list should only contain his accounts."""
        resp = await seeded_txn_client.get("/accounts", headers=rajesh_headers)
        assert resp.status_code == 200
        data = resp.json()
        items = data.get("items", data) if isinstance(data, dict) else data
        assert isinstance(items, list)
        assert len(items) == 3  # Shop Cash, ICICI, Paytm

    async def test_rajesh_sees_only_his_customers(self, seeded_ledger_client, rajesh_headers):
        """Rajesh's customer list should only contain his 4 customers."""
        resp = await seeded_ledger_client.get("/customers", headers=rajesh_headers)
        assert resp.status_code == 200
        data = resp.json()
        items = data.get("items", data) if isinstance(data, dict) else data
        assert isinstance(items, list)
        assert len(items) == 4

    async def test_anita_sees_only_her_customers(self, seeded_ledger_client, anita_headers):
        """Anita's customer list should only contain her 4 customers."""
        resp = await seeded_ledger_client.get("/customers", headers=anita_headers)
        assert resp.status_code == 200
        data = resp.json()
        items = data.get("items", data) if isinstance(data, dict) else data
        assert isinstance(items, list)
        assert len(items) == 4


# ===========================================================================
# Inactive User Lockout
# ===========================================================================
class TestInactiveUserLockout:
    async def test_meena_cannot_access_profile(self, seeded_user_client, meena_headers):
        """Inactive user (Meena) should be rejected by user-service."""
        resp = await seeded_user_client.get("/users/me", headers=meena_headers)
        assert resp.status_code in (401, 403)

    async def test_meena_cannot_list_transactions(self, seeded_txn_client, meena_headers):
        """Inactive user (Meena) should be rejected by transaction-service."""
        resp = await seeded_txn_client.get("/transactions", headers=meena_headers)
        assert resp.status_code in (401, 403)

    async def test_meena_cannot_list_customers(self, seeded_ledger_client, meena_headers):
        """Inactive user (Meena) should be rejected by ledger-service."""
        resp = await seeded_ledger_client.get("/customers", headers=meena_headers)
        assert resp.status_code in (401, 403)


# ===========================================================================
# Account Balance Integrity
# ===========================================================================
class TestAccountBalances:
    async def test_priya_has_correct_account_types(self, seeded_txn_client, priya_headers):
        """Priya should have cash, bank, and credit_card accounts."""
        resp = await seeded_txn_client.get("/accounts", headers=priya_headers)
        assert resp.status_code == 200
        data = resp.json()
        accounts = data.get("items", data) if isinstance(data, dict) else data
        types = {a["type"] for a in accounts}
        assert types == {"cash", "bank", "credit_card"}

    async def test_rajesh_has_business_account_types(self, seeded_txn_client, rajesh_headers):
        """Rajesh should have cash, bank, and wallet accounts."""
        resp = await seeded_txn_client.get("/accounts", headers=rajesh_headers)
        assert resp.status_code == 200
        data = resp.json()
        accounts = data.get("items", data) if isinstance(data, dict) else data
        types = {a["type"] for a in accounts}
        assert types == {"cash", "bank", "wallet"}

    async def test_priya_credit_card_negative_balance(self, seeded_txn_client, priya_headers):
        """Priya's credit card should have a negative balance."""
        resp = await seeded_txn_client.get("/accounts", headers=priya_headers)
        assert resp.status_code == 200
        data = resp.json()
        accounts = data.get("items", data) if isinstance(data, dict) else data
        cc = [a for a in accounts if a["type"] == "credit_card"]
        assert len(cc) == 1
        assert Decimal(str(cc[0]["balance"])) < 0


# ===========================================================================
# Ledger Customer Counts
# ===========================================================================
class TestLedgerCustomerCounts:
    async def test_rajesh_has_4_customers(self, seeded_ledger_client, rajesh_headers):
        resp = await seeded_ledger_client.get("/customers", headers=rajesh_headers)
        assert resp.status_code == 200
        data = resp.json()
        items = data.get("items", data) if isinstance(data, dict) else data
        assert len(items) == 4

    async def test_anita_has_4_customers(self, seeded_ledger_client, anita_headers):
        resp = await seeded_ledger_client.get("/customers", headers=anita_headers)
        assert resp.status_code == 200
        data = resp.json()
        items = data.get("items", data) if isinstance(data, dict) else data
        assert len(items) == 4


# ===========================================================================
# Edge Cases
# ===========================================================================
class TestEdgeCases:
    async def test_arjun_usd_account(self, seeded_txn_client, arjun_headers):
        """Arjun has a USD wallet."""
        resp = await seeded_txn_client.get("/accounts", headers=arjun_headers)
        assert resp.status_code == 200
        data = resp.json()
        accounts = data.get("items", data) if isinstance(data, dict) else data
        assert len(accounts) == 1
        assert accounts[0]["currency"] == "USD"
        assert accounts[0]["type"] == "wallet"

    async def test_vikram_minimal_data(self, seeded_txn_client, vikram_headers):
        """Vikram has only 1 cash account."""
        resp = await seeded_txn_client.get("/accounts", headers=vikram_headers)
        assert resp.status_code == 200
        data = resp.json()
        accounts = data.get("items", data) if isinstance(data, dict) else data
        assert len(accounts) == 1
        assert accounts[0]["type"] == "cash"

    async def test_arjun_no_phone(self, seeded_user_client, arjun_headers):
        """Arjun has no phone number."""
        resp = await seeded_user_client.get("/users/me", headers=arjun_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["phone"] is None

    async def test_categories_include_system(self, seeded_txn_client, priya_headers):
        """Category list should include system categories."""
        resp = await seeded_txn_client.get("/categories", headers=priya_headers)
        assert resp.status_code == 200
        data = resp.json()
        cats = data.get("items", data) if isinstance(data, dict) else data
        system_cats = [c for c in cats if c.get("is_system")]
        assert len(system_cats) >= 29


# ===========================================================================
# Scope Enforcement (require_scope permission boundaries)
# All three test users operate in Rajesh's Business Org:
#   Priya  → accountant (accounts:read, transactions:read, ledger:*, reports:read — no :write on accounts/txn)
#   Anita  → staff      (accounts:read, transactions:read/write, ledger:* — no accounts:write)
#   Vikram → read_only  (all :read scopes only)
# ===========================================================================
class TestScopeEnforcement:
    # --- accountant: has accounts:read, no accounts:write, no transactions:write ---

    async def test_accountant_can_read_accounts(self, seeded_txn_client, priya_as_accountant_headers):
        """Accountant must be able to list accounts (accounts:read)."""
        resp = await seeded_txn_client.get("/accounts", headers=priya_as_accountant_headers)
        assert resp.status_code == 200

    async def test_accountant_cannot_create_account(self, seeded_txn_client, priya_as_accountant_headers):
        """Accountant must be blocked from creating accounts (no accounts:write)."""
        resp = await seeded_txn_client.post(
            "/accounts",
            json={"name": "New Account", "type": "cash", "currency": "INR"},
            headers=priya_as_accountant_headers,
        )
        assert resp.status_code == 403

    async def test_accountant_can_read_transactions(self, seeded_txn_client, priya_as_accountant_headers):
        """Accountant must be able to list transactions (transactions:read)."""
        resp = await seeded_txn_client.get("/transactions", headers=priya_as_accountant_headers)
        assert resp.status_code == 200

    async def test_accountant_cannot_create_transaction(self, seeded_txn_client, priya_as_accountant_headers):
        """Accountant must be blocked from creating transactions (no transactions:write)."""
        resp = await seeded_txn_client.post(
            "/transactions",
            json={
                "account_id": ACCOUNT_RAJESH_BIZ_CASH_ID,
                "category_id": CAT_SALARY_ID,
                "type": "income",
                "amount": "1000.00",
                "transaction_date": "2026-01-01T10:00:00Z",
            },
            headers=priya_as_accountant_headers,
        )
        assert resp.status_code == 403

    # --- staff: has transactions:write, accounts:read but no accounts:write ---

    async def test_staff_can_read_accounts(self, seeded_txn_client, anita_as_staff_headers):
        """Staff must be able to list accounts (accounts:read)."""
        resp = await seeded_txn_client.get("/accounts", headers=anita_as_staff_headers)
        assert resp.status_code == 200

    async def test_staff_cannot_create_account(self, seeded_txn_client, anita_as_staff_headers):
        """Staff must be blocked from creating accounts (no accounts:write)."""
        resp = await seeded_txn_client.post(
            "/accounts",
            json={"name": "Staff Account", "type": "cash", "currency": "INR"},
            headers=anita_as_staff_headers,
        )
        assert resp.status_code == 403

    async def test_staff_can_create_transaction(self, seeded_txn_client, anita_as_staff_headers):
        """Staff must be able to create transactions (transactions:write)."""
        resp = await seeded_txn_client.post(
            "/transactions",
            json={
                "account_id": ACCOUNT_RAJESH_BIZ_CASH_ID,
                "category_id": CAT_SALARY_ID,
                "type": "income",
                "amount": "5000.00",
                "transaction_date": "2026-01-15T10:00:00Z",
            },
            headers=anita_as_staff_headers,
        )
        # 201 = scope passed + transaction created; not 403 = scope check passed
        assert resp.status_code in (201, 200)

    # --- read_only: only :read scopes ---

    async def test_read_only_can_read_accounts(self, seeded_txn_client, vikram_as_read_only_headers):
        """Read-only member must be able to list accounts (accounts:read)."""
        resp = await seeded_txn_client.get("/accounts", headers=vikram_as_read_only_headers)
        assert resp.status_code == 200

    async def test_read_only_cannot_create_account(self, seeded_txn_client, vikram_as_read_only_headers):
        """Read-only member must be blocked from creating accounts (no accounts:write)."""
        resp = await seeded_txn_client.post(
            "/accounts",
            json={"name": "Readonly Account", "type": "cash", "currency": "INR"},
            headers=vikram_as_read_only_headers,
        )
        assert resp.status_code == 403

    async def test_read_only_cannot_create_transaction(self, seeded_txn_client, vikram_as_read_only_headers):
        """Read-only member must be blocked from creating transactions (no transactions:write)."""
        resp = await seeded_txn_client.post(
            "/transactions",
            json={
                "account_id": ACCOUNT_RAJESH_BIZ_CASH_ID,
                "category_id": CAT_SALARY_ID,
                "type": "expense",
                "amount": "100.00",
                "transaction_date": "2026-01-15T10:00:00Z",
            },
            headers=vikram_as_read_only_headers,
        )
        assert resp.status_code == 403
