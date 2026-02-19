import sys
from pathlib import Path
import uuid as _uuid_mod
from collections.abc import AsyncGenerator
from datetime import datetime, timezone
from decimal import Decimal

import pytest
from httpx import ASGITransport, AsyncClient
from jose import jwt
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

# Ensure service root is on path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from config import settings
from models.base import Base
from models.user import User
from models.account import Account  # noqa: F401 — register with Base
from models.category import Category
from models.transaction import Transaction

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
        email="aiuser@example.com",
        password_hash="not_used",
        full_name="AI Test User",
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
async def seed_categories(db_session: AsyncSession) -> list[Category]:
    """Seed system categories for categorization tests."""
    cats = [
        Category(id=_uuid_mod.uuid4(), user_id=None, name="Groceries", type="expense", icon="cart", is_system=True),
        Category(id=_uuid_mod.uuid4(), user_id=None, name="Transport", type="expense", icon="car", is_system=True),
        Category(id=_uuid_mod.uuid4(), user_id=None, name="Salary", type="income", icon="briefcase", is_system=True),
        Category(id=_uuid_mod.uuid4(), user_id=None, name="Food & Dining", type="expense", icon="utensils", is_system=True),
        Category(id=_uuid_mod.uuid4(), user_id=None, name="Shopping", type="expense", icon="bag", is_system=True),
        Category(id=_uuid_mod.uuid4(), user_id=None, name="Utilities", type="expense", icon="zap", is_system=True),
        Category(id=_uuid_mod.uuid4(), user_id=None, name="Freelance", type="income", icon="laptop", is_system=True),
    ]
    for c in cats:
        db_session.add(c)
        await db_session.flush()
    return cats


@pytest.fixture
async def seed_transactions(db_session: AsyncSession, seed_user: User, seed_categories: list[Category]) -> list[Transaction]:
    """Seed transactions for insights tests."""
    from datetime import timedelta

    now = datetime.now(timezone.utc)
    cat_by_name = {c.name: c for c in seed_categories}
    acct = Account(
        id=_uuid_mod.uuid4(), user_id=seed_user.id, name="Test Cash",
        type="cash", currency="INR", balance=Decimal("10000.00"), is_active=True,
    )
    db_session.add(acct)
    await db_session.flush()

    txns = [
        # Last 30 days — expenses
        Transaction(id=_uuid_mod.uuid4(), user_id=seed_user.id, account_id=acct.id,
                    category_id=cat_by_name["Groceries"].id, type="expense",
                    amount=Decimal("2500.00"), description="Weekly groceries",
                    transaction_date=now - timedelta(days=5)),
        Transaction(id=_uuid_mod.uuid4(), user_id=seed_user.id, account_id=acct.id,
                    category_id=cat_by_name["Transport"].id, type="expense",
                    amount=Decimal("800.00"), description="Uber rides",
                    transaction_date=now - timedelta(days=10)),
        Transaction(id=_uuid_mod.uuid4(), user_id=seed_user.id, account_id=acct.id,
                    category_id=cat_by_name["Food & Dining"].id, type="expense",
                    amount=Decimal("1200.00"), description="Restaurant dinner",
                    transaction_date=now - timedelta(days=15)),
        # Last 30 days — income
        Transaction(id=_uuid_mod.uuid4(), user_id=seed_user.id, account_id=acct.id,
                    category_id=cat_by_name["Salary"].id, type="income",
                    amount=Decimal("50000.00"), description="Monthly salary",
                    transaction_date=now - timedelta(days=2)),
        # Previous 30 days — expenses (for trend comparison)
        Transaction(id=_uuid_mod.uuid4(), user_id=seed_user.id, account_id=acct.id,
                    category_id=cat_by_name["Groceries"].id, type="expense",
                    amount=Decimal("1000.00"), description="Groceries prev month",
                    transaction_date=now - timedelta(days=40)),
        Transaction(id=_uuid_mod.uuid4(), user_id=seed_user.id, account_id=acct.id,
                    category_id=cat_by_name["Transport"].id, type="expense",
                    amount=Decimal("600.00"), description="Metro prev month",
                    transaction_date=now - timedelta(days=45)),
    ]
    for t in txns:
        db_session.add(t)
        await db_session.flush()
    return txns
