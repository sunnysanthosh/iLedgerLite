import uuid
from collections.abc import AsyncGenerator
from datetime import datetime, timezone

import pytest
from config import settings
from httpx import ASGITransport, AsyncClient
from jose import jwt
from models.audit_log import AuditLog  # noqa: F401 — register with Base
from models.base import Base
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
    """Create a valid access token for testing."""
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
    """Create a test user + personal org in the database and return the user."""
    from models.org import Organisation, OrgMembership

    user = User(
        id=uuid.uuid4(),
        email="testuser@example.com",
        password_hash="hashed_not_used_in_user_service",
        full_name="Test User",
        phone="+911234567890",
        is_active=True,
    )
    db_session.add(user)
    await db_session.flush()

    org = Organisation(
        id=uuid.uuid4(),
        name="Test User's Personal",
        owner_id=user.id,
        is_personal=True,
        is_active=True,
    )
    db_session.add(org)
    await db_session.flush()

    membership = OrgMembership(
        id=uuid.uuid4(),
        org_id=org.id,
        user_id=user.id,
        role="owner",
        is_active=True,
    )
    db_session.add(membership)
    await db_session.flush()
    await db_session.refresh(user)
    return user


@pytest.fixture
def auth_headers(seed_user: User) -> dict:
    """Authorization headers with a valid access token for seed_user."""
    token = make_access_token(str(seed_user.id))
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
async def seed_full_data(db_session: AsyncSession):
    """Seed all shared test users + settings into the user-service test DB."""
    from models.user_settings import UserSettings

    from shared.test_data import USER_SETTINGS, USERS

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

    for s in USER_SETTINGS:
        setting = UserSettings(
            id=s["id"],
            user_id=s["user_id"],
            account_type=s["account_type"],
            currency=s["currency"],
            language=s["language"],
            business_category=s["business_category"],
            notifications_enabled=s["notifications_enabled"],
            onboarding_completed=s["onboarding_completed"],
        )
        db_session.add(setting)
    await db_session.flush()
