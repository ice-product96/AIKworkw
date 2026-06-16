import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from unittest.mock import AsyncMock, patch

from app.core.database import Base, get_db
from app.core.security import hash_password
from app.main import app
from app.models import User, UserRole

TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

engine = create_async_engine(TEST_DATABASE_URL, echo=False)
TestSessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


@pytest.fixture(scope="session")
def event_loop():
    import asyncio
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(autouse=True)
async def setup_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture(autouse=True)
async def mock_redis():
    class MockPipeline:
        def __init__(self, redis):
            self.redis = redis

        def sadd(self, *args, **kwargs):
            return self

        def expire(self, *args, **kwargs):
            return self

        async def execute(self):
            return []

    mock = AsyncMock()
    mock.get = AsyncMock(return_value=None)
    mock.setex = AsyncMock(return_value=True)
    mock.lpush = AsyncMock(return_value=1)
    mock.rpop = AsyncMock(return_value=None)
    mock.smembers = AsyncMock(return_value=set())
    mock.sadd = AsyncMock(return_value=1)
    mock.expire = AsyncMock(return_value=True)
    mock.execute = AsyncMock(return_value=[])
    mock.pipeline = lambda: MockPipeline(mock)
    with patch("app.services.matching.get_redis_pool", return_value=mock), patch(
        "app.api.v1.agent_api.get_redis_pool", return_value=mock
    ):
        yield mock


async def override_get_db():
    async with TestSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


app.dependency_overrides[get_db] = override_get_db


@pytest_asyncio.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest_asyncio.fixture
async def client_user() -> dict:
    async with TestSessionLocal() as session:
        user = User(
            email="client@test.com",
            password_hash=hash_password("password123"),
            role=UserRole.client,
        )
        session.add(user)
        await session.commit()
        return {"email": "client@test.com", "password": "password123"}
