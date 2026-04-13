import asyncio
import os
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

TEST_DB_PATH = Path(__file__).resolve().parent / "test_dubnewsai.db"

# Force an isolated, offline-friendly test environment instead of inheriting
# whichever production variables happen to be loaded in the shell.
os.environ["DATABASE_URL"] = f"sqlite+aiosqlite:///{TEST_DB_PATH.as_posix()}"
os.environ["SECRET_KEY"] = "test-secret-key"
os.environ["LOG_LEVEL"] = "WARNING"
os.environ["ENVIRONMENT"] = "test"
os.environ["ENABLE_EMBEDDED_SYNC"] = "false"
os.environ["REDIS_URL"] = "redis://127.0.0.1:6399/0"

from app.main import app  # noqa: E402
import app.models as app_models  # noqa: E402,F401
from app.models.base import Base  # noqa: E402
from app.database import engine  # noqa: E402


async def reset_database() -> None:
    await engine.dispose()
    if TEST_DB_PATH.exists():
        TEST_DB_PATH.unlink()
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)


@pytest.fixture(autouse=True)
def fresh_database() -> None:
    asyncio.run(reset_database())
    yield


@pytest.fixture(scope="session", autouse=True)
def cleanup_database() -> None:
    yield
    if TEST_DB_PATH.exists():
        TEST_DB_PATH.unlink()


@pytest.fixture
def client() -> TestClient:
    with TestClient(app) as test_client:
        yield test_client
