import asyncio
import os
import sys
from pathlib import Path

from sqlalchemy import select

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from app.core.security import get_password_hash
from app.database import AsyncSessionLocal
from app.models.market_data import MarketType, StockExchange, WatchlistSymbol
from app.models.subscription import Subscription
from app.models.user import User, UserRole
from app.models.user_preference import UserPreference


DEFAULT_ADMIN_EMAIL = "admin@dubnewsai.com"
DEFAULT_ADMIN_NAME = "DUBNEWSAI Admin"
DEFAULT_ADMIN_PASSWORD = "xcxcdfdferer123"


WATCHLIST = [
    {
        "symbol": "EMAAR",
        "name": "Emaar Properties",
        "market_type": MarketType.STOCK,
        "exchange": StockExchange.DFM,
        "is_real_estate_company": True,
        "priority": 10,
    },
    {
        "symbol": "DAMAC",
        "name": "Damac Properties",
        "market_type": MarketType.STOCK,
        "exchange": StockExchange.DFM,
        "is_real_estate_company": True,
        "priority": 9,
    },
    {
        "symbol": "ALDAR",
        "name": "Aldar Properties",
        "market_type": MarketType.STOCK,
        "exchange": StockExchange.ADX,
        "is_real_estate_company": True,
        "priority": 9,
    },
    {
        "symbol": "DEYAAR",
        "name": "Deyaar Development",
        "market_type": MarketType.STOCK,
        "exchange": StockExchange.DFM,
        "is_real_estate_company": True,
        "priority": 7,
    },
    {
        "symbol": "AMLAK",
        "name": "Amlak Finance",
        "market_type": MarketType.STOCK,
        "exchange": StockExchange.DFM,
        "is_real_estate_company": True,
        "priority": 6,
    },
    {
        "symbol": "UPP",
        "name": "Union Properties",
        "market_type": MarketType.STOCK,
        "exchange": StockExchange.DFM,
        "is_real_estate_company": True,
        "priority": 6,
    },
    {
        "symbol": "ESHRAQ",
        "name": "Eshraq Investments",
        "market_type": MarketType.STOCK,
        "exchange": StockExchange.ADX,
        "is_real_estate_company": True,
        "priority": 5,
    },
    {
        "symbol": "RAKPROP",
        "name": "RAK Properties",
        "market_type": MarketType.STOCK,
        "exchange": StockExchange.ADX,
        "is_real_estate_company": True,
        "priority": 5,
    },
    {
        "symbol": "^DFM",
        "name": "Dubai Financial Market General Index",
        "market_type": MarketType.INDEX,
        "exchange": StockExchange.DFM,
        "is_real_estate_company": False,
        "priority": 10,
    },
]


async def seed_production() -> None:
    admin_email = os.getenv("SEED_ADMIN_EMAIL", DEFAULT_ADMIN_EMAIL).lower()
    admin_name = os.getenv("SEED_ADMIN_NAME", DEFAULT_ADMIN_NAME)
    admin_password = os.getenv("SEED_ADMIN_PASSWORD", DEFAULT_ADMIN_PASSWORD)

    print("Seeding production database...\n")

    async with AsyncSessionLocal() as session:
        result = await session.execute(select(User).where(User.email == admin_email))
        admin_user = result.scalar_one_or_none()

        if admin_user is None:
            admin_user = User(
                email=admin_email,
                full_name=admin_name,
                hashed_password=get_password_hash(admin_password),
                role=UserRole.ADMIN,
                is_active=True,
                is_verified=True,
            )
            session.add(admin_user)
            await session.flush()
            session.add(UserPreference(user_id=admin_user.id))
            session.add(Subscription(user_id=admin_user.id))

            print(f"OK Admin user created: {admin_email}")
            print(f"  Password: {admin_password}")
            print("  WARNING: CHANGE THIS PASSWORD AFTER FIRST LOGIN!\n")
        else:
            print(f"OK Admin user already exists: {admin_email}\n")

        created_symbols = 0
        existing_symbols = 0
        for item in WATCHLIST:
            existing = await session.execute(
                select(WatchlistSymbol).where(WatchlistSymbol.symbol == item["symbol"])
            )
            watchlist_symbol = existing.scalar_one_or_none()

            if watchlist_symbol is None:
                session.add(WatchlistSymbol(**item))
                created_symbols += 1
                print(f"OK Added watchlist symbol: {item['symbol']}")
            else:
                existing_symbols += 1
                print(f"OK Watchlist symbol already exists: {item['symbol']}")

        await session.commit()

    print("\nProduction seeding complete!")


if __name__ == "__main__":
    asyncio.run(seed_production())
