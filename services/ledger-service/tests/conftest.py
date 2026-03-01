import uuid
from collections.abc import AsyncGenerator
from datetime import datetime, timezone

import pytest
from config import settings
from httpx import ASGITransport, AsyncClient
from jose import jwt
from models.base import Base
from models.customer import Customer
from models.user import User
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

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
        email="ledgeruser@example.com",
        password_hash="not_used",
        full_name="Ledger User",
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
async def seed_customer(db_session: AsyncSession, seed_user: User) -> Customer:
    customer = Customer(
        id=uuid.uuid4(),
        user_id=seed_user.id,
        name="Test Customer",
        phone="+919876543210",
        email="customer@example.com",
        address="123 Test Street",
    )
    db_session.add(customer)
    await db_session.flush()
    await db_session.refresh(customer)
    return customer


@pytest.fixture
async def seed_full_data(db_session: AsyncSession):
    """Seed all shared test data into the ledger-service test DB."""
    from models.ledger_entry import LedgerEntry

    from shared.test_data import CUSTOMERS, LEDGER_ENTRIES, USERS

    for u in USERS:
        user = User(
            id=u["id"],
            email=u["email"],
            password_hash=u["password_hash"],
            full_name=u["full_name"],
            phone=u["phone"],
            is_active=u["is_active"],
        )
        db_session.add(user)
    await db_session.flush()

    for c in CUSTOMERS:
        cust = Customer(
            id=c["id"],
            user_id=c["user_id"],
            name=c["name"],
            phone=c["phone"],
            email=c["email"],
            address=c["address"],
        )
        db_session.add(cust)
    await db_session.flush()

    for e in LEDGER_ENTRIES:
        entry = LedgerEntry(
            id=e["id"],
            user_id=e["user_id"],
            customer_id=e["customer_id"],
            type=e["type"],
            amount=e["amount"],
            description=e["description"],
            due_date=e["due_date"],
            is_settled=e["is_settled"],
        )
        db_session.add(entry)
    await db_session.flush()
