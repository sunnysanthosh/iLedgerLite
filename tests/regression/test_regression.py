"""
Regression Tests — cross-service data integrity checks with seeded data.

Runs in-process using ASGI test clients with SQLite + seed data.
Run with: cd C:/Temp/LedgerLite && pytest tests/regression/ -v
"""

import pytest
from decimal import Decimal

from shared.test_data import (
    USER_PRIYA_ID, USER_RAJESH_ID, USER_ANITA_ID,
    USER_VIKRAM_ID, USER_MEENA_ID, USER_ARJUN_ID,
    RAW_PASSWORD,
)


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
