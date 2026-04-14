from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.rate_limit import check_tiered_rate_limit
from app.database import get_db
from app.dependencies import get_current_user_optional
from app.models.market_data import MarketType
from app.schemas.intelligence import (
    ComparativeAnalysisRequest,
    ComparativeAnalysisResponse,
    PropertyValuationRequest,
    PropertyValuationResponse,
    ROIRequest,
    ROIResponse,
)
from app.models.user import User
from app.schemas.market_data import CurrencyRateResponse, EconomicIndicatorResponse, MarketDataResponse, MarketOverview, WeatherSnapshotResponse
from app.services.aggregation.market_aggregator import COMMODITY_SYMBOLS, GLOBAL_REALESTATE_SYMBOLS, UAE_CORE_SYMBOLS, market_aggregator
from app.services.intelligence.property_valuation_service import property_valuation
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
    payload = await MarketService.get_market_overview_payload(db)
    return MarketOverview.model_validate(payload)


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
    data = await MarketService.get_priority_market_board(db, limit=limit)
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
    await MarketService.ensure_canonical_watchlist(db)
    data = await MarketService.get_real_estate_companies(db)
    return [MarketDataResponse.model_validate(item) for item in data]


@router.get("/global-real-estate", response_model=list[MarketDataResponse])
async def get_global_real_estate_board(
    request: Request,
    limit: int = Query(default=16, ge=1, le=50),
    db: AsyncSession = Depends(get_db),
    current_user: User | None = Depends(get_current_user_optional),
    _rate_limit: None = Depends(check_tiered_rate_limit),
) -> list[MarketDataResponse]:
    """Get the global real-estate benchmark board."""
    del request, current_user
    data = await MarketService.get_global_real_estate_board(db, limit=limit)
    return [MarketDataResponse.model_validate(item) for item in data]


@router.get("/indices", response_model=list[MarketDataResponse])
async def get_market_indices(
    request: Request,
    limit: int = Query(default=10, ge=1, le=20),
    db: AsyncSession = Depends(get_db),
    current_user: User | None = Depends(get_current_user_optional),
    _rate_limit: None = Depends(check_tiered_rate_limit),
) -> list[MarketDataResponse]:
    """Get the current market index board."""
    del request, current_user
    data = await MarketService.get_market_indices(db, limit=limit)
    return [MarketDataResponse.model_validate(item) for item in data]


@router.get("/commodities", response_model=list[MarketDataResponse])
async def get_market_commodities(
    request: Request,
    limit: int = Query(default=10, ge=1, le=20),
    db: AsyncSession = Depends(get_db),
    current_user: User | None = Depends(get_current_user_optional),
    _rate_limit: None = Depends(check_tiered_rate_limit),
) -> list[MarketDataResponse]:
    """Get the current commodity board."""
    del request, current_user
    data = await MarketService.get_market_commodities(db, limit=limit)
    return [MarketDataResponse.model_validate(item) for item in data]


@router.get("/currencies", response_model=list[CurrencyRateResponse])
async def get_market_currencies(
    request: Request,
    limit: int = Query(default=10, ge=1, le=20),
    db: AsyncSession = Depends(get_db),
    current_user: User | None = Depends(get_current_user_optional),
    _rate_limit: None = Depends(check_tiered_rate_limit),
) -> list[CurrencyRateResponse]:
    """Get the current FX board."""
    del request, current_user
    data = await MarketService.get_latest_currency_rates(db, limit=limit)
    return [CurrencyRateResponse.model_validate(item) for item in data]


@router.get("/provider-utilization")
async def get_market_provider_utilization(
    request: Request,
    limit: int = Query(default=8, ge=1, le=20),
    db: AsyncSession = Depends(get_db),
    current_user: User | None = Depends(get_current_user_optional),
    _rate_limit: None = Depends(check_tiered_rate_limit),
) -> list[dict]:
    """Get market provider utilization for board diagnostics."""
    del request, current_user
    return await MarketService.get_provider_utilization_summary(db, limit=limit)


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


@router.get("/weather", response_model=WeatherSnapshotResponse | None)
async def get_market_weather(
    request: Request,
    current_user: User | None = Depends(get_current_user_optional),
    _rate_limit: None = Depends(check_tiered_rate_limit),
) -> WeatherSnapshotResponse | None:
    """Get current Dubai market weather."""
    del request, current_user
    data = await MarketService.get_market_weather()
    if data is None:
        return None
    return WeatherSnapshotResponse.model_validate(data)


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


@router.post("/property-valuation/estimate", response_model=PropertyValuationResponse)
async def estimate_property_value(
    payload: PropertyValuationRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User | None = Depends(get_current_user_optional),
    _rate_limit: None = Depends(check_tiered_rate_limit),
) -> PropertyValuationResponse:
    del current_user
    data = await property_valuation.estimate_property_value(
        db,
        area_sqft=payload.area_sqft,
        bedrooms=payload.bedrooms,
        location=payload.location,
        property_type=payload.property_type,
        year_built=payload.year_built,
        amenities=payload.amenities,
    )
    return PropertyValuationResponse.model_validate(data)


@router.get("/property-valuation/options")
async def get_property_valuation_options(
    db: AsyncSession = Depends(get_db),
    current_user: User | None = Depends(get_current_user_optional),
    _rate_limit: None = Depends(check_tiered_rate_limit),
) -> dict:
    del current_user
    return await property_valuation.get_property_options(db)


@router.get("/property-valuation/preset")
async def get_property_valuation_preset(
    location: str = Query(..., min_length=2),
    property_type: str = Query(default="Apartment"),
    db: AsyncSession = Depends(get_db),
    current_user: User | None = Depends(get_current_user_optional),
    _rate_limit: None = Depends(check_tiered_rate_limit),
) -> dict:
    del current_user
    return await property_valuation.get_property_preset(db, location=location, property_type=property_type)


@router.post("/property-valuation/roi", response_model=ROIResponse)
async def calculate_property_roi(
    payload: ROIRequest,
    current_user: User | None = Depends(get_current_user_optional),
    _rate_limit: None = Depends(check_tiered_rate_limit),
) -> ROIResponse:
    del current_user
    data = await property_valuation.calculate_roi(
        purchase_price=payload.purchase_price,
        rental_income_monthly=payload.rental_income_monthly,
        expenses_monthly=payload.expenses_monthly,
        appreciation_rate=payload.appreciation_rate,
    )
    return ROIResponse.model_validate(data)


@router.post("/property-valuation/comparative-analysis", response_model=ComparativeAnalysisResponse)
async def get_comparative_market_analysis(
    payload: ComparativeAnalysisRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User | None = Depends(get_current_user_optional),
    _rate_limit: None = Depends(check_tiered_rate_limit),
) -> ComparativeAnalysisResponse:
    del current_user
    data = await property_valuation.comparative_market_analysis(
        db,
        location=payload.location,
        property_type=payload.property_type,
        bedrooms=payload.bedrooms,
        area_sqft=payload.area_sqft,
        year_built=payload.year_built,
        radius_km=payload.radius_km,
    )
    return ComparativeAnalysisResponse.model_validate(data)
