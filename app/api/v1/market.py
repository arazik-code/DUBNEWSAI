from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.rate_limit import check_tiered_rate_limit
from app.database import get_db
from app.dependencies import get_current_user_optional
from app.models.market_data import MarketType
from app.models.user import User
from app.schemas.market_data import EconomicIndicatorResponse, MarketDataResponse, MarketOverview
from app.services.aggregation.market_aggregator import COMMODITY_SYMBOLS, GLOBAL_REALESTATE_SYMBOLS, UAE_CORE_SYMBOLS
from app.services.market_service import MarketService

router = APIRouter(prefix="/market", tags=["market"])


@router.get("/overview", response_model=MarketOverview)
async def get_market_overview(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User | None = Depends(get_current_user_optional),
    _rate_limit: None = Depends(check_tiered_rate_limit),
) -> MarketOverview:
    """Get full market overview.

    **Public Access:** Yes
    """
    del request, current_user
    stocks = await MarketService.get_latest_market_data_for_symbols(
        db,
        [item.symbol for item in UAE_CORE_SYMBOLS],
        limit=20,
        include_watchlist_fallback=True,
    )
    indices = await MarketService.get_latest_market_data(db, MarketType.INDEX, limit=10)
    global_real_estate = await MarketService.get_latest_market_data_for_symbols(
        db,
        [item.symbol for item in GLOBAL_REALESTATE_SYMBOLS],
        limit=8,
    )
    commodities = await MarketService.get_latest_market_data_for_symbols(
        db,
        [item.symbol for item in COMMODITY_SYMBOLS],
        limit=6,
    )
    real_estate = await MarketService.get_real_estate_companies(db)
    currencies = await MarketService.get_latest_currency_rates(db, limit=10)
    economic_indicators = await MarketService.get_latest_economic_indicators(db, limit=12)
    return MarketOverview(
        stocks=[MarketDataResponse.model_validate(item) for item in stocks],
        indices=[MarketDataResponse.model_validate(item) for item in indices],
        global_real_estate=[MarketDataResponse.model_validate(item) for item in global_real_estate],
        commodities=[MarketDataResponse.model_validate(item) for item in commodities],
        currencies=currencies,
        economic_indicators=[EconomicIndicatorResponse.model_validate(item) for item in economic_indicators],
        real_estate_companies=[MarketDataResponse.model_validate(item) for item in real_estate],
    )


@router.get("/stocks", response_model=list[MarketDataResponse])
async def get_stocks(
    request: Request,
    limit: int = Query(default=50, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User | None = Depends(get_current_user_optional),
    _rate_limit: None = Depends(check_tiered_rate_limit),
) -> list[MarketDataResponse]:
    """Get latest stock data.

    **Public Access:** Yes
    """
    del request, current_user
    data = await MarketService.get_latest_market_data(db, MarketType.STOCK, limit=limit)
    return [MarketDataResponse.model_validate(item) for item in data]


@router.get("/real-estate-companies", response_model=list[MarketDataResponse])
async def get_real_estate_companies(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User | None = Depends(get_current_user_optional),
    _rate_limit: None = Depends(check_tiered_rate_limit),
) -> list[MarketDataResponse]:
    """Get real-estate company market data.

    **Public Access:** Yes
    """
    del request, current_user
    data = await MarketService.get_real_estate_companies(db)
    return [MarketDataResponse.model_validate(item) for item in data]


@router.get("/economic-indicators", response_model=list[EconomicIndicatorResponse])
async def get_economic_indicators(
    request: Request,
    limit: int = Query(default=12, ge=1, le=50),
    db: AsyncSession = Depends(get_db),
    current_user: User | None = Depends(get_current_user_optional),
    _rate_limit: None = Depends(check_tiered_rate_limit),
) -> list[EconomicIndicatorResponse]:
    """Get latest macro and economic indicators."""
    del request, current_user
    data = await MarketService.get_latest_economic_indicators(db, limit=limit)
    return [EconomicIndicatorResponse.model_validate(item) for item in data]


@router.get("/symbol/{symbol}", response_model=MarketDataResponse)
async def get_symbol_data(
    request: Request,
    symbol: str,
    db: AsyncSession = Depends(get_db),
    current_user: User | None = Depends(get_current_user_optional),
    _rate_limit: None = Depends(check_tiered_rate_limit),
) -> MarketDataResponse:
    """Get data for a single symbol.

    **Public Access:** Yes
    """
    del request, current_user
    data = await MarketService.get_latest_symbol_data(db, symbol)
    if data is None:
        raise HTTPException(status_code=404, detail="Symbol not found")
    return MarketDataResponse.model_validate(data)
