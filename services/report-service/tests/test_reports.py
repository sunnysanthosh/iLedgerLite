"""Report service tests using shared seed data.

Primary test user: Rajesh (USER_RAJESH_ID) — has both transactions AND ledger entries.
Secondary: Priya (USER_PRIYA_ID) — transactions only, no ledger.
"""
from decimal import Decimal

import pytest

from shared.test_data import (
    USER_PRIYA_ID,
    USER_RAJESH_ID,
    ANCHOR_DATE,
    get_transactions_for_user,
    get_customers_for_user,
    get_ledger_entries_for_customer,
    get_outstanding_balance,
    get_accounts_for_user,
    make_auth_headers,
    rajesh_headers,
    priya_headers,
    ALL_CATEGORIES,
)


# ──── Health ────

async def test_health(client):
    resp = await client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["service"] == "report"


# ──── Auth required ────

async def test_reports_require_auth(client):
    endpoints = ["/reports/profit-loss", "/reports/cashflow", "/reports/budget", "/reports/summary", "/reports/export"]
    for ep in endpoints:
        resp = await client.get(ep)
        assert resp.status_code == 401, f"{ep} should require auth"


# ──── Profit & Loss ────

async def test_profit_loss_rajesh(client, seed_full_data):
    """Rajesh: income=141000, expense=152000 (includes transfer=20000 as transfer type)."""
    headers = rajesh_headers()
    resp = await client.get(
        "/reports/profit-loss",
        params={"start_date": "2025-01-01", "end_date": "2026-12-31"},
        headers=headers,
    )
    assert resp.status_code == 200
    data = resp.json()
    # Rajesh: 7 income txns = 141000, 10 expense txns = 152000 (1 transfer excluded)
    assert Decimal(data["total_income"]) == Decimal("141000.00")
    assert Decimal(data["total_expenses"]) == Decimal("152000.00")
    assert Decimal(data["net_profit"]) == Decimal("-11000.00")


async def test_profit_loss_priya(client, seed_full_data):
    """Priya: income=153200, expense=61147."""
    headers = priya_headers()
    resp = await client.get(
        "/reports/profit-loss",
        params={"start_date": "2025-01-01", "end_date": "2026-12-31"},
        headers=headers,
    )
    assert resp.status_code == 200
    data = resp.json()
    assert Decimal(data["total_income"]) == Decimal("153200.00")
    assert Decimal(data["total_expenses"]) == Decimal("61147.00")
    assert Decimal(data["net_profit"]) == Decimal("92053.00")
    assert len(data["income_by_category"]) == 4  # Salary, Freelance, Tuition, Investment
    assert len(data["expense_by_category"]) == 11


async def test_profit_loss_empty_range(client, seed_full_data):
    """No transactions in a date range should return zeroes."""
    headers = priya_headers()
    resp = await client.get(
        "/reports/profit-loss",
        params={"start_date": "2020-01-01", "end_date": "2020-01-31"},
        headers=headers,
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["total_income"] == "0.00"
    assert data["total_expenses"] == "0.00"
    assert data["net_profit"] == "0.00"


# ──── Cashflow ────

async def test_cashflow_monthly(client, seed_full_data):
    """Rajesh's transactions span ~90 days, should produce multiple monthly buckets."""
    headers = rajesh_headers()
    resp = await client.get(
        "/reports/cashflow",
        params={"start_date": "2025-01-01", "end_date": "2026-12-31", "period": "monthly"},
        headers=headers,
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["period"] == "monthly"
    assert len(data["periods"]) >= 2
    assert Decimal(data["total_inflows"]) == Decimal("141000.00")
    assert Decimal(data["total_outflows"]) == Decimal("152000.00")


async def test_cashflow_daily(client, seed_full_data):
    headers = rajesh_headers()
    resp = await client.get(
        "/reports/cashflow",
        params={"start_date": "2025-01-01", "end_date": "2026-12-31", "period": "daily"},
        headers=headers,
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["period"] == "daily"
    assert len(data["periods"]) > 0


async def test_cashflow_weekly(client, seed_full_data):
    headers = rajesh_headers()
    resp = await client.get(
        "/reports/cashflow",
        params={"start_date": "2025-01-01", "end_date": "2026-12-31", "period": "weekly"},
        headers=headers,
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["period"] == "weekly"


async def test_cashflow_invalid_period(client, seed_full_data):
    headers = rajesh_headers()
    resp = await client.get(
        "/reports/cashflow",
        params={"start_date": "2025-01-01", "end_date": "2026-12-31", "period": "yearly"},
        headers=headers,
    )
    assert resp.status_code == 422


# ──── Budget ────

async def test_budget_report_rajesh(client, seed_full_data):
    """Rajesh has 7 expense categories totaling 152000."""
    headers = rajesh_headers()
    resp = await client.get(
        "/reports/budget",
        params={"start_date": "2025-01-01", "end_date": "2026-12-31"},
        headers=headers,
    )
    assert resp.status_code == 200
    data = resp.json()
    assert Decimal(data["total_spent"]) == Decimal("152000.00")
    assert len(data["categories"]) == 7


async def test_budget_report_priya(client, seed_full_data):
    """Priya has 11 expense categories totaling 61147."""
    headers = priya_headers()
    resp = await client.get(
        "/reports/budget",
        params={"start_date": "2025-01-01", "end_date": "2026-12-31"},
        headers=headers,
    )
    assert resp.status_code == 200
    data = resp.json()
    assert Decimal(data["total_spent"]) == Decimal("61147.00")
    assert len(data["categories"]) == 11


async def test_budget_empty_range(client, seed_full_data):
    headers = priya_headers()
    resp = await client.get(
        "/reports/budget",
        params={"start_date": "2020-01-01", "end_date": "2020-01-31"},
        headers=headers,
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["total_spent"] == "0.00"
    assert len(data["categories"]) == 0


# ──── Summary ────

async def test_summary_rajesh(client, seed_full_data):
    """Rajesh: 3 active accounts, 18 txns, has ledger receivables."""
    headers = rajesh_headers()
    resp = await client.get("/reports/summary", headers=headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["account_count"] == 3
    assert Decimal(data["total_balance"]) == Decimal("183000.00")
    assert data["transaction_count"] == 18
    assert Decimal(data["total_income"]) == Decimal("141000.00")
    assert Decimal(data["total_expenses"]) == Decimal("152000.00")
    # Rajesh ledger: unsettled debits=78500, unsettled credits=17500
    assert Decimal(data["outstanding_receivables"]) == Decimal("78500.00")
    assert Decimal(data["outstanding_payables"]) == Decimal("17500.00")


async def test_summary_priya(client, seed_full_data):
    """Priya: 3 active accounts, 20 txns, no ledger entries."""
    headers = priya_headers()
    resp = await client.get("/reports/summary", headers=headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["account_count"] == 3
    assert Decimal(data["total_balance"]) == Decimal("87500.50")
    assert data["transaction_count"] == 20
    assert data["outstanding_receivables"] == "0.00"
    assert data["outstanding_payables"] == "0.00"


async def test_summary_no_data(client, auth_headers):
    """User with no transactions should return zeroes."""
    resp = await client.get("/reports/summary", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["total_balance"] == "0.00"
    assert data["transaction_count"] == 0


# ──── Export ────

async def test_export_csv_rajesh(client, seed_full_data):
    """Rajesh has 18 transactions total; wide range should export all."""
    headers = rajesh_headers()
    resp = await client.get(
        "/reports/export",
        params={"start_date": "2025-01-01", "end_date": "2026-12-31", "format": "csv"},
        headers=headers,
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["format"] == "csv"
    assert data["content_type"] == "text/csv"
    assert "ID,Date,Type,Amount,Category,Account,Description" in data["data"]
    lines = data["data"].strip().split("\n")
    assert len(lines) == 19  # header + 18 data rows


async def test_export_empty_range(client, seed_full_data):
    headers = rajesh_headers()
    resp = await client.get(
        "/reports/export",
        params={"start_date": "2020-01-01", "end_date": "2020-01-31", "format": "csv"},
        headers=headers,
    )
    assert resp.status_code == 200
    data = resp.json()
    lines = data["data"].strip().split("\n")
    assert len(lines) == 1  # header only


async def test_export_invalid_format(client, seed_full_data):
    headers = rajesh_headers()
    resp = await client.get(
        "/reports/export",
        params={"start_date": "2025-01-01", "end_date": "2025-12-31", "format": "pdf"},
        headers=headers,
    )
    assert resp.status_code == 422
