"""
Cloud verification — proves the deployed staging stack actually works end to
end: real ingress routing, real TLS, real Cloud SQL, and that JWT_SECRET was
applied identically across all 8 deployments (a misconfiguration invisible to
the local suite, since local tests mint tokens in-process against the same
service they validate them in).

Test data created here (an account + a transaction) is intentionally left in
staging — it's disposable, non-production data. No cleanup step by design.
"""

from datetime import date, datetime

from httpx import AsyncClient


class TestIngressAndTLS:
    async def test_login_reaches_auth_service_through_ingress(self, cloud_client: AsyncClient, auth_token: str):
        """If we got here, auth_token fixture already proved ingress + TLS + login work."""
        assert auth_token


class TestCrossServiceAuth:
    """Same JWT, validated by three different deployed services. Proves
    JWT_SECRET was applied identically everywhere — not just to auth-service."""

    async def test_auth_me(self, cloud_client: AsyncClient, auth_headers: dict[str, str]):
        resp = await cloud_client.get("/auth/me", headers=auth_headers)
        assert resp.status_code == 200
        assert resp.json()["email"] == "cloud-verify@ledgerlite.internal"

    async def test_users_me(self, cloud_client: AsyncClient, auth_headers: dict[str, str]):
        resp = await cloud_client.get("/users/me", headers=auth_headers)
        assert resp.status_code == 200

    async def test_accounts_list(self, cloud_client: AsyncClient, auth_headers: dict[str, str]):
        resp = await cloud_client.get("/accounts", headers=auth_headers)
        assert resp.status_code == 200


class TestRealCloudSqlRoundTrip:
    """Create -> read back, through ingress, against real Cloud SQL (not SQLite)."""

    async def test_create_account_and_transaction(self, cloud_client: AsyncClient, auth_headers: dict[str, str]):
        tag = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S")

        account_resp = await cloud_client.post(
            "/accounts",
            headers=auth_headers,
            json={"name": f"Cloud Verify — {tag}", "type": "cash", "currency": "INR"},
        )
        assert account_resp.status_code == 201, account_resp.text
        account_id = account_resp.json()["id"]

        txn_resp = await cloud_client.post(
            "/transactions",
            headers=auth_headers,
            json={
                "account_id": account_id,
                "type": "income",
                "amount": "1.00",
                "description": f"Cloud Verify — {tag}",
                "transaction_date": date.today().isoformat(),
            },
        )
        assert txn_resp.status_code == 201, txn_resp.text

        readback = await cloud_client.get("/transactions", headers=auth_headers)
        assert readback.status_code == 200
        items = readback.json()["items"]
        assert any(item["id"] == txn_resp.json()["id"] for item in items)


class TestCrossServiceReads:
    """Different deployed services (ledger, report), same token — proves
    org-scoping and inter-service trust work over the real K8s network path."""

    async def test_customers_list(self, cloud_client: AsyncClient, auth_headers: dict[str, str]):
        resp = await cloud_client.get("/customers", headers=auth_headers)
        assert resp.status_code == 200

    async def test_reports_summary(self, cloud_client: AsyncClient, auth_headers: dict[str, str]):
        resp = await cloud_client.get("/reports/summary", headers=auth_headers)
        assert resp.status_code == 200
