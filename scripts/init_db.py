import asyncio
from pathlib import Path
import sys

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from alembic import command
from alembic.config import Config

from app.config import get_settings
from app.models import *  # noqa: F401,F403
from app.models.base import Base
from app.database import engine


async def bootstrap_sqlite() -> None:
    settings = get_settings()
    database_url = settings.DATABASE_URL

    sqlite_path = database_url.replace("sqlite+aiosqlite:///", "", 1)
    db_file = Path(sqlite_path)
    db_file.parent.mkdir(parents=True, exist_ok=True)

    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)

    await engine.dispose()


def migrate_postgres() -> None:
    alembic_cfg = Config("alembic.ini")
    command.upgrade(alembic_cfg, "head")


async def main() -> None:
    settings = get_settings()
    if settings.DATABASE_URL.startswith("sqlite+aiosqlite:///"):
        await bootstrap_sqlite()
        return

    await asyncio.to_thread(migrate_postgres)


if __name__ == "__main__":
    asyncio.run(main())
