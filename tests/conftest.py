"""
Root-level test conftest for smoke and regression tests.

Runs in-process against each service's FastAPI app using ASGI test clients
and per-service SQLite in-memory databases. No Docker required.

Module isolation: each service has identically-named packages (models, db,
main, config, etc.). We manage sys.path and sys.modules to avoid clashes.
"""

import importlib
import sys
import uuid as _uuid
from collections.abc import AsyncGenerator
from pathlib import Path

import fakeredis.aioredis
import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from shared.test_data import (
    ACCOUNTS,
    ALL_CATEGORIES,
    CUSTOMERS,
    LEDGER_ENTRIES,
    ORG_ANITA_ID,
    ORG_ARJUN_ID,
    ORG_MEENA_ID,
    ORG_MEMBERSHIPS,
    ORG_PRIYA_ID,
    ORG_RAJESH_ID,
    ORG_VIKRAM_ID,
    ORGANISATIONS,
    TRANSACTIONS,
    USER_ANITA_ID,
    USER_ARJUN_ID,
    USER_MEENA_ID,
    USER_PRIYA_ID,
    USER_RAJESH_ID,
    USER_SETTINGS,
    USER_VIKRAM_ID,
    USERS,
    make_auth_headers,
)

# ---------------------------------------------------------------------------
# Module isolation helpers
# ---------------------------------------------------------------------------
SERVICES_DIR = Path(__file__).resolve().parent.parent / "services"
ALL_SERVICE_DIRS = ["auth-service", "user-service", "transaction-service", "ledger-service"]
SERVICE_MODULE_PREFIXES = ("models", "routers", "services", "schemas", "db", "config", "main")


def _clear_service_modules():
    """Remove service-local modules from sys.modules to allow clean reimport."""
    to_remove = [
        name
        for name in list(sys.modules)
        if any(name == p or name.startswith(p + ".") for p in SERVICE_MODULE_PREFIXES)
    ]
    for name in to_remove:
        del sys.modules[name]


def _activate_service(service_dir: str):
    """Switch sys.path to point exclusively to the given service directory."""
    _clear_service_modules()
    target = str(SERVICES_DIR / service_dir)
    others = {str(SERVICES_DIR / d) for d in ALL_SERVICE_DIRS if d != service_dir}
    sys.path = [p for p in sys.path if p not in others]
    if target not in sys.path:
        sys.path.insert(0, target)


def _uid(s):
    """Convert string UUID to uuid.UUID object. Passes through None."""
    if s is None:
        return None
    return _uuid.UUID(s) if isinstance(s, str) else s


# ---------------------------------------------------------------------------
# Session-scoped engines (one per service, persists across all tests)
# ---------------------------------------------------------------------------
@pytest.fixture(scope="session")
def auth_engine():
    return create_async_engine("sqlite+aiosqlite:///:memory:", echo=False, use_insertmanyvalues=False)


@pytest.fixture(scope="session")
def user_engine():
    return create_async_engine("sqlite+aiosqlite:///:memory:", echo=False, use_insertmanyvalues=False)


@pytest.fixture(scope="session")
def txn_engine():
    return create_async_engine("sqlite+aiosqlite:///:memory:", echo=False, use_insertmanyvalues=False)


@pytest.fixture(scope="session")
def ledger_engine():
    return create_async_engine("sqlite+aiosqlite:///:memory:", echo=False, use_insertmanyvalues=False)


# ---------------------------------------------------------------------------
# Session-scoped table creation
# ---------------------------------------------------------------------------
_bases = {}  # Store Base references for teardown


@pytest.fixture(scope="session", autouse=True)
async def create_all_tables(auth_engine, user_engine, txn_engine, ledger_engine):
    """Create tables for all 4 services, managing module imports carefully."""
    configs = [
        ("auth", "auth-service", auth_engine, ["models.user"]),
        ("user", "user-service", user_engine, ["models.user", "models.user_settings"]),
        (
            "txn",
            "transaction-service",
            txn_engine,
            ["models.user", "models.org", "models.account", "models.category", "models.transaction"],
        ),
        (
            "ledger",
            "ledger-service",
            ledger_engine,
            ["models.user", "models.org", "models.customer", "models.ledger_entry"],
        ),
    ]

    for svc_name, svc_dir, engine, model_modules in configs:
        _activate_service(svc_dir)
        importlib.import_module("models.base")
        for mod_name in model_modules:
            importlib.import_module(mod_name)
        Base = sys.modules["models.base"].Base
        _bases[svc_name] = Base
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    yield

    for svc_name, _, _, engine, _ in [
        ("auth", "auth-service", auth_engine, auth_engine, None),
        ("user", "user-service", user_engine, user_engine, None),
        ("txn", "transaction-service", txn_engine, txn_engine, None),
        ("ledger", "ledger-service", ledger_engine, ledger_engine, None),
    ]:
        async with engine.begin() as conn:
            await conn.run_sync(_bases[svc_name].metadata.drop_all)


# ---------------------------------------------------------------------------
# Per-test DB session fixtures
# ---------------------------------------------------------------------------
@pytest.fixture
async def auth_db(auth_engine) -> AsyncGenerator[AsyncSession, None]:
    sm = async_sessionmaker(auth_engine, class_=AsyncSession, expire_on_commit=False)
    async with auth_engine.begin() as conn:
        session = sm(bind=conn)
        try:
            yield session
        finally:
            await session.close()
            await conn.rollback()


@pytest.fixture
async def user_db(user_engine) -> AsyncGenerator[AsyncSession, None]:
    sm = async_sessionmaker(user_engine, class_=AsyncSession, expire_on_commit=False)
    async with user_engine.begin() as conn:
        session = sm(bind=conn)
        try:
            yield session
        finally:
            await session.close()
            await conn.rollback()


@pytest.fixture
async def txn_db(txn_engine) -> AsyncGenerator[AsyncSession, None]:
    sm = async_sessionmaker(txn_engine, class_=AsyncSession, expire_on_commit=False)
    async with txn_engine.begin() as conn:
        session = sm(bind=conn)
        try:
            yield session
        finally:
            await session.close()
            await conn.rollback()


@pytest.fixture
async def ledger_db(ledger_engine) -> AsyncGenerator[AsyncSession, None]:
    sm = async_sessionmaker(ledger_engine, class_=AsyncSession, expire_on_commit=False)
    async with ledger_engine.begin() as conn:
        session = sm(bind=conn)
        try:
            yield session
        finally:
            await session.close()
            await conn.rollback()


@pytest.fixture
def fake_redis():
    return fakeredis.aioredis.FakeRedis(decode_responses=True)


# ===========================================================================
# Seeded ASGI clients
# ===========================================================================


@pytest.fixture
async def seeded_auth_client(auth_db, fake_redis) -> AsyncGenerator[AsyncClient, None]:
    """Auth-service client with all seed users pre-loaded."""
    _activate_service("auth-service")
    from models.user import User

    for u in USERS:
        auth_db.add(
            User(
                id=_uid(u["id"]),
                email=u["email"],
                password_hash=u["password_hash"],
                full_name=u["full_name"],
                phone=u["phone"],
                is_active=u["is_active"],
            )
        )
    await auth_db.flush()

    from db.session import get_db
    from main import app
    from services.redis_client import get_redis

    async def override_db():
        yield auth_db

    async def override_redis():
        yield fake_redis

    app.dependency_overrides[get_db] = override_db
    app.dependency_overrides[get_redis] = override_redis

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture
async def seeded_user_client(user_db) -> AsyncGenerator[AsyncClient, None]:
    """User-service client with all seed users + settings pre-loaded."""
    _activate_service("user-service")
    from models.user import User
    from models.user_settings import UserSettings

    for u in USERS:
        user_db.add(
            User(
                id=_uid(u["id"]),
                email=u["email"],
                password_hash=u["password_hash"],
                full_name=u["full_name"],
                phone=u["phone"],
                is_active=u["is_active"],
            )
        )
    await user_db.flush()

    for s in USER_SETTINGS:
        user_db.add(
            UserSettings(
                id=_uid(s["id"]),
                user_id=_uid(s["user_id"]),
                account_type=s["account_type"],
                currency=s["currency"],
                language=s["language"],
                business_category=s["business_category"],
                notifications_enabled=s["notifications_enabled"],
                onboarding_completed=s["onboarding_completed"],
            )
        )
    await user_db.flush()

    from db.session import get_db
    from main import app

    async def override_db():
        yield user_db

    app.dependency_overrides[get_db] = override_db

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture
async def seeded_txn_client(txn_db) -> AsyncGenerator[AsyncClient, None]:
    """Transaction-service client with all seed data pre-loaded."""
    _activate_service("transaction-service")
    from models.account import Account
    from models.category import Category
    from models.org import Organisation, OrgMembership
    from models.transaction import Transaction
    from models.user import User

    for u in USERS:
        txn_db.add(
            User(
                id=_uid(u["id"]),
                email=u["email"],
                password_hash=u["password_hash"],
                full_name=u["full_name"],
                phone=u["phone"],
                is_active=u["is_active"],
            )
        )
    await txn_db.flush()

    for o in ORGANISATIONS:
        txn_db.add(
            Organisation(
                id=_uid(o["id"]),
                name=o["name"],
                owner_id=_uid(o["owner_id"]),
                is_personal=o["is_personal"],
                is_active=o["is_active"],
            )
        )
    await txn_db.flush()

    for m in ORG_MEMBERSHIPS:
        txn_db.add(
            OrgMembership(
                id=_uid(m["id"]),
                org_id=_uid(m["org_id"]),
                user_id=_uid(m["user_id"]),
                role=m["role"],
                is_active=m["is_active"],
            )
        )
    await txn_db.flush()

    for a in ACCOUNTS:
        txn_db.add(
            Account(
                id=_uid(a["id"]),
                user_id=_uid(a["user_id"]),
                org_id=_uid(a["org_id"]),
                name=a["name"],
                type=a["type"],
                currency=a["currency"],
                balance=a["balance"],
                is_active=a["is_active"],
            )
        )
    await txn_db.flush()

    for c in ALL_CATEGORIES:
        txn_db.add(
            Category(
                id=_uid(c["id"]),
                user_id=_uid(c["user_id"]),
                name=c["name"],
                type=c["type"],
                icon=c["icon"],
                is_system=c["is_system"],
            )
        )
    await txn_db.flush()

    for t in TRANSACTIONS:
        txn_db.add(
            Transaction(
                id=_uid(t["id"]),
                user_id=_uid(t["user_id"]),
                org_id=_uid(t["org_id"]),
                account_id=_uid(t["account_id"]),
                category_id=_uid(t["category_id"]),
                type=t["type"],
                amount=t["amount"],
                description=t["description"],
                transaction_date=t["transaction_date"],
            )
        )
    await txn_db.flush()

    from db.session import get_db
    from main import app

    async def override_db():
        yield txn_db

    app.dependency_overrides[get_db] = override_db

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture
async def seeded_ledger_client(ledger_db) -> AsyncGenerator[AsyncClient, None]:
    """Ledger-service client with all seed data pre-loaded."""
    _activate_service("ledger-service")
    from models.customer import Customer
    from models.ledger_entry import LedgerEntry
    from models.org import Organisation, OrgMembership
    from models.user import User

    for u in USERS:
        ledger_db.add(
            User(
                id=_uid(u["id"]),
                email=u["email"],
                password_hash=u["password_hash"],
                full_name=u["full_name"],
                phone=u["phone"],
                is_active=u["is_active"],
            )
        )
    await ledger_db.flush()

    for o in ORGANISATIONS:
        ledger_db.add(
            Organisation(
                id=_uid(o["id"]),
                name=o["name"],
                owner_id=_uid(o["owner_id"]),
                is_personal=o["is_personal"],
                is_active=o["is_active"],
            )
        )
    await ledger_db.flush()

    for m in ORG_MEMBERSHIPS:
        ledger_db.add(
            OrgMembership(
                id=_uid(m["id"]),
                org_id=_uid(m["org_id"]),
                user_id=_uid(m["user_id"]),
                role=m["role"],
                is_active=m["is_active"],
            )
        )
    await ledger_db.flush()

    for c in CUSTOMERS:
        ledger_db.add(
            Customer(
                id=_uid(c["id"]),
                user_id=_uid(c["user_id"]),
                org_id=_uid(c["org_id"]),
                name=c["name"],
                phone=c["phone"],
                email=c["email"],
                address=c["address"],
            )
        )
    await ledger_db.flush()

    for e in LEDGER_ENTRIES:
        ledger_db.add(
            LedgerEntry(
                id=_uid(e["id"]),
                user_id=_uid(e["user_id"]),
                org_id=_uid(e["org_id"]),
                customer_id=_uid(e["customer_id"]),
                type=e["type"],
                amount=e["amount"],
                description=e["description"],
                due_date=e["due_date"],
                is_settled=e["is_settled"],
            )
        )
    await ledger_db.flush()

    from db.session import get_db
    from main import app

    async def override_db():
        yield ledger_db

    app.dependency_overrides[get_db] = override_db

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c
    app.dependency_overrides.clear()


# ===========================================================================
# Per-user auth header fixtures (include X-Org-ID for org-scoped endpoints)
# ===========================================================================
@pytest.fixture(scope="session")
def priya_headers():
    return make_auth_headers(USER_PRIYA_ID, org_id=ORG_PRIYA_ID)


@pytest.fixture(scope="session")
def rajesh_headers():
    return make_auth_headers(USER_RAJESH_ID, org_id=ORG_RAJESH_ID)


@pytest.fixture(scope="session")
def anita_headers():
    return make_auth_headers(USER_ANITA_ID, org_id=ORG_ANITA_ID)


@pytest.fixture(scope="session")
def vikram_headers():
    return make_auth_headers(USER_VIKRAM_ID, org_id=ORG_VIKRAM_ID)


@pytest.fixture(scope="session")
def meena_headers():
    return make_auth_headers(USER_MEENA_ID, org_id=ORG_MEENA_ID)


@pytest.fixture(scope="session")
def arjun_headers():
    return make_auth_headers(USER_ARJUN_ID, org_id=ORG_ARJUN_ID)
