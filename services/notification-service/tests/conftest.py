import uuid as _uuid_mod
from collections.abc import AsyncGenerator
from datetime import datetime, timezone

import pytest
from config import settings
from httpx import ASGITransport, AsyncClient
from jose import jwt
from models.base import Base
from models.customer import Customer  # noqa: F401 — register with Base
from models.ledger_entry import LedgerEntry  # noqa: F401
from models.notification import Notification
from models.org import Organisation, OrgMembership  # noqa: F401 — register with Base
from models.user import User
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

TEST_DB_URL = "sqlite+aiosqlite:///:memory:"
engine = create_async_engine(TEST_DB_URL, echo=False)
TestSessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


def _id(val):
    """Convert string UUID to uuid.UUID for SQLite compatibility."""
    if val is None:
        return None
    return _uuid_mod.UUID(val) if isinstance(val, str) else val


@pytest.fixture(scope="session", autouse=True)
async def create_tables():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    async with engine.begin() as conn:
        session = TestSessionLocal(bind=conn)
        try:
            yield session
        finally:
            await session.close()
            await conn.rollback()


@pytest.fixture
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    from db.session import get_db
    from main import app

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()


def make_access_token(user_id: str) -> str:
    payload = {
        "sub": user_id,
        "type": "access",
        "exp": int(datetime.now(timezone.utc).timestamp()) + 3600,
        "iat": int(datetime.now(timezone.utc).timestamp()),
        "jti": str(_uuid_mod.uuid4()),
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


@pytest.fixture
async def seed_user(db_session: AsyncSession) -> User:
    """Standalone user for simple auth-only tests."""
    user = User(
        id=_uuid_mod.uuid4(),
        email="notifuser@example.com",
        password_hash="not_used",
        full_name="Notification User",
        phone="+911234567890",
        is_active=True,
    )
    db_session.add(user)
    await db_session.flush()

    org = Organisation(
        id=_uuid_mod.uuid4(),
        name="Notification User's Personal",
        owner_id=user.id,
        is_personal=True,
        is_active=True,
    )
    db_session.add(org)
    await db_session.flush()

    membership = OrgMembership(
        id=_uuid_mod.uuid4(),
        org_id=org.id,
        user_id=user.id,
        role="owner",
        is_active=True,
    )
    db_session.add(membership)
    await db_session.flush()

    user._org_id = org.id  # type: ignore[attr-defined]  # transient Python attr
    await db_session.refresh(user)
    return user


@pytest.fixture
def auth_headers(seed_user: User) -> dict:
    token = make_access_token(str(seed_user.id))
    return {
        "Authorization": f"Bearer {token}",
        "X-Org-ID": str(seed_user._org_id),  # type: ignore[attr-defined]
    }


@pytest.fixture
async def seed_full_data(db_session: AsyncSession):
    """Seed shared users, customers, and ledger entries from shared.test_data."""
    from shared.test_data import (
        CUSTOMERS,
        LEDGER_ENTRIES,
        ORG_ANITA_ID,
        ORG_ARJUN_ID,
        ORG_MEENA_ID,
        ORG_MEMBER_IDS,
        ORG_PRIYA_ID,
        ORG_RAJESH_ID,
        ORG_VIKRAM_ID,
        USER_ORG_MAP,
        USERS,
    )

    org_ids = [ORG_PRIYA_ID, ORG_RAJESH_ID, ORG_ANITA_ID, ORG_VIKRAM_ID, ORG_MEENA_ID, ORG_ARJUN_ID]
    for u, org_id_str, member_id_str in zip(USERS, org_ids, ORG_MEMBER_IDS):
        db_session.add(
            User(
                id=_id(u["id"]),
                email=u["email"],
                password_hash=u["password_hash"],
                full_name=u["full_name"],
                phone=u["phone"],
                is_active=u["is_active"],
            )
        )
        await db_session.flush()

        db_session.add(
            Organisation(
                id=_id(org_id_str),
                name=f"{u['full_name']}'s Personal",
                owner_id=_id(u["id"]),
                is_personal=True,
                is_active=True,
            )
        )
        await db_session.flush()

        db_session.add(
            OrgMembership(
                id=_id(member_id_str),
                org_id=_id(org_id_str),
                user_id=_id(u["id"]),
                role="owner",
                is_active=True,
            )
        )
        await db_session.flush()

    for c in CUSTOMERS:
        db_session.add(
            Customer(
                id=_id(c["id"]),
                user_id=_id(c["user_id"]),
                org_id=_id(USER_ORG_MAP[c["user_id"]]),
                name=c["name"],
                phone=c["phone"],
                email=c["email"],
                address=c["address"],
            )
        )
        await db_session.flush()

    for e in LEDGER_ENTRIES:
        db_session.add(
            LedgerEntry(
                id=_id(e["id"]),
                user_id=_id(e["user_id"]),
                org_id=_id(USER_ORG_MAP[e["user_id"]]),
                customer_id=_id(e["customer_id"]),
                type=e["type"],
                amount=e["amount"],
                description=e["description"],
                due_date=e["due_date"],
                is_settled=e["is_settled"],
            )
        )
        await db_session.flush()


@pytest.fixture
async def seed_customer_no_balance(db_session: AsyncSession, seed_full_data) -> Customer:
    """A customer belonging to Rajesh with no ledger entries (zero outstanding)."""
    from shared.test_data import ORG_RAJESH_ID, USER_RAJESH_ID

    cust = Customer(
        id=_uuid_mod.uuid4(),
        user_id=_id(USER_RAJESH_ID),
        org_id=_id(ORG_RAJESH_ID),
        name="Test Zero-Balance Customer",
        phone="+910000000000",
        email=None,
        address=None,
    )
    db_session.add(cust)
    await db_session.flush()
    await db_session.refresh(cust)
    return cust


@pytest.fixture
async def seed_notifications(db_session: AsyncSession, seed_full_data) -> list[Notification]:
    """Create test notifications for Rajesh (from shared seed data)."""
    from shared.test_data import CUST_SURESH_TEXTILES_ID, ORG_RAJESH_ID, USER_RAJESH_ID

    notifs = [
        Notification(
            id=_uuid_mod.uuid4(),
            user_id=_id(USER_RAJESH_ID),
            org_id=_id(ORG_RAJESH_ID),
            type="system",
            title="Welcome",
            message="Welcome to LedgerLite!",
            is_read=True,
        ),
        Notification(
            id=_uuid_mod.uuid4(),
            user_id=_id(USER_RAJESH_ID),
            org_id=_id(ORG_RAJESH_ID),
            type="reminder",
            title="Payment due",
            message="Suresh Textiles owes 23000",
            is_read=False,
            related_entity_id=_id(CUST_SURESH_TEXTILES_ID),
        ),
        Notification(
            id=_uuid_mod.uuid4(),
            user_id=_id(USER_RAJESH_ID),
            org_id=_id(ORG_RAJESH_ID),
            type="overdue",
            title="Overdue payment",
            message="Lakshmi Stores payment overdue",
            is_read=False,
        ),
    ]
    for n in notifs:
        db_session.add(n)
        await db_session.flush()
    return notifs
