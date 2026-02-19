import uuid
from collections.abc import AsyncGenerator
from datetime import datetime, timezone
from decimal import Decimal

import pytest
from httpx import ASGITransport, AsyncClient
from jose import jwt
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from config import settings
from models.account import Account
from models.base import Base
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
        "jti": str(uuid.uuid4()),
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


@pytest.fixture
async def seed_user(db_session: AsyncSession) -> User:
    user = User(
        id=uuid.uuid4(),
        email="txnuser@example.com",
        password_hash="not_used",
        full_name="Transaction User",
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
    account = Account(
        id=uuid.uuid4(),
        user_id=seed_user.id,
        name="Cash Wallet",
        type="cash",
        currency="INR",
        balance=Decimal("1000.00"),
        is_active=True,
    )
    db_session.add(account)
    await db_session.flush()
    await db_session.refresh(account)
    return account


@pytest.fixture
async def seed_full_data(db_session: AsyncSession):
    """Seed all shared test data into the transaction-service test DB."""
    from models.category import Category
    from models.transaction import Transaction
    from shared.test_data import USERS, ACCOUNTS, ALL_CATEGORIES, TRANSACTIONS

    for u in USERS:
        user = User(
            id=u["id"], email=u["email"], password_hash=u["password_hash"],
            full_name=u["full_name"], phone=u["phone"], is_active=u["is_active"],
        )
        db_session.add(user)
    await db_session.flush()

    for a in ACCOUNTS:
        acct = Account(
            id=a["id"], user_id=a["user_id"], name=a["name"],
            type=a["type"], currency=a["currency"],
            balance=a["balance"], is_active=a["is_active"],
        )
        db_session.add(acct)
    await db_session.flush()

    for c in ALL_CATEGORIES:
        cat = Category(
            id=c["id"], user_id=c["user_id"], name=c["name"],
            type=c["type"], icon=c["icon"], is_system=c["is_system"],
        )
        db_session.add(cat)
    await db_session.flush()

    for t in TRANSACTIONS:
        txn = Transaction(
            id=t["id"], user_id=t["user_id"], account_id=t["account_id"],
            category_id=t["category_id"], type=t["type"],
            amount=t["amount"], description=t["description"],
            transaction_date=t["transaction_date"],
        )
        db_session.add(txn)
    await db_session.flush()
