import uuid as _uuid_mod
from collections.abc import AsyncGenerator
from datetime import datetime, timezone

import pytest
from httpx import ASGITransport, AsyncClient
from jose import jwt
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from config import settings
from models.base import Base
from models.user import User
from models.account import Account  # noqa: F401 — register with Base
from models.category import Category  # noqa: F401
from models.customer import Customer  # noqa: F401
from models.ledger_entry import LedgerEntry  # noqa: F401
from models.transaction import Transaction  # noqa: F401

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
    user = User(
        id=_uuid_mod.uuid4(),
        email="reportuser@example.com",
        password_hash="not_used",
        full_name="Report User",
        phone="+911234567890",
        is_active=True,
    )
    db_session.add(user)
    await db_session.flush()
    await db_session.refresh(user)
    return user


@pytest.fixture
def auth_headers(seed_user: User) -> dict:
    token = make_access_token(str(seed_user.id))
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
async def seed_full_data(db_session: AsyncSession):
    """Seed all shared test data into the report-service test DB."""
    from shared.test_data import (
        ACCOUNTS, ALL_CATEGORIES, CUSTOMERS, LEDGER_ENTRIES, TRANSACTIONS, USERS,
    )

    for u in USERS:
        db_session.add(User(
            id=_id(u["id"]), email=u["email"], password_hash=u["password_hash"],
            full_name=u["full_name"], phone=u["phone"], is_active=u["is_active"],
        ))
        await db_session.flush()

    for a in ACCOUNTS:
        db_session.add(Account(
            id=_id(a["id"]), user_id=_id(a["user_id"]), name=a["name"],
            type=a["type"], currency=a["currency"],
            balance=a["balance"], is_active=a["is_active"],
        ))
        await db_session.flush()

    for c in ALL_CATEGORIES:
        db_session.add(Category(
            id=_id(c["id"]), user_id=_id(c["user_id"]), name=c["name"],
            type=c["type"], icon=c["icon"], is_system=c["is_system"],
        ))
        await db_session.flush()

    for t in TRANSACTIONS:
        db_session.add(Transaction(
            id=_id(t["id"]), user_id=_id(t["user_id"]), account_id=_id(t["account_id"]),
            category_id=_id(t["category_id"]), type=t["type"],
            amount=t["amount"], description=t["description"],
            transaction_date=t["transaction_date"],
        ))
        await db_session.flush()

    for c in CUSTOMERS:
        db_session.add(Customer(
            id=_id(c["id"]), user_id=_id(c["user_id"]), name=c["name"],
            phone=c["phone"], email=c["email"], address=c["address"],
        ))
        await db_session.flush()

    for e in LEDGER_ENTRIES:
        db_session.add(LedgerEntry(
            id=_id(e["id"]), user_id=_id(e["user_id"]), customer_id=_id(e["customer_id"]),
            type=e["type"], amount=e["amount"], description=e["description"],
            due_date=e["due_date"], is_settled=e["is_settled"],
        ))
        await db_session.flush()
