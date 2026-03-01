import sys
import uuid as _uuid_mod
from collections.abc import AsyncGenerator
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path

import pytest
from httpx import ASGITransport, AsyncClient
from jose import jwt
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from config import settings
from models.account import Account
from models.base import Base
from models.customer import Customer
from models.sync_log import SyncLog  # noqa: F401 — register with Base
from models.transaction import Transaction
from models.user import User

TEST_DB_URL = "sqlite+aiosqlite:///:memory:"
engine = create_async_engine(TEST_DB_URL, echo=False)
TestSessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


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
        email="syncuser@example.com",
        password_hash="not_used",
        full_name="Sync Test User",
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
async def seed_account(db_session: AsyncSession, seed_user: User) -> Account:
    acct = Account(
        id=_uuid_mod.uuid4(),
        user_id=seed_user.id,
        name="Sync Test Cash",
        type="cash",
        currency="INR",
        balance=Decimal("5000.00"),
        is_active=True,
    )
    db_session.add(acct)
    await db_session.flush()
    await db_session.refresh(acct)
    return acct


@pytest.fixture
async def seed_customer(db_session: AsyncSession, seed_user: User) -> Customer:
    cust = Customer(
        id=_uuid_mod.uuid4(),
        user_id=seed_user.id,
        name="Sync Test Customer",
        phone="+910000000001",
    )
    db_session.add(cust)
    await db_session.flush()
    await db_session.refresh(cust)
    return cust


@pytest.fixture
async def seed_server_transactions(
    db_session: AsyncSession,
    seed_user: User,
    seed_account: Account,
) -> list[Transaction]:
    """Create server-side transactions for pull tests."""
    now = datetime.now(timezone.utc)
    txns = [
        Transaction(
            id=_uuid_mod.uuid4(),
            user_id=seed_user.id,
            account_id=seed_account.id,
            type="expense",
            amount=Decimal("500.00"),
            description="Server expense 1",
            transaction_date=now - timedelta(days=2),
        ),
        Transaction(
            id=_uuid_mod.uuid4(),
            user_id=seed_user.id,
            account_id=seed_account.id,
            type="income",
            amount=Decimal("10000.00"),
            description="Server salary",
            transaction_date=now - timedelta(days=1),
        ),
    ]
    for t in txns:
        db_session.add(t)
        await db_session.flush()
    return txns
