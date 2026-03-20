from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.rate_limit import check_tiered_rate_limit
from app.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.schemas.portfolio import (
    InvestmentScoreRequest,
    InvestmentScoreResponse,
    PortfolioAnalyticsResponse,
    PortfolioCreateRequest,
    PortfolioResponse,
    PortfolioTransactionCreateRequest,
    PortfolioTransactionResponse,
    WatchlistCreateRequest,
    WatchlistItemCreateRequest,
    WatchlistItemResponse,
    WatchlistResponse,
)
from app.services.portfolio.investment_scoring_service import investment_scoring
from app.services.portfolio.portfolio_service import portfolio_service

router = APIRouter(prefix="/portfolios", tags=["portfolios"])


@router.get("/", response_model=list[PortfolioResponse])
async def list_portfolios(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    _rate_limit: None = Depends(check_tiered_rate_limit),
) -> list[PortfolioResponse]:
    portfolios = await portfolio_service.list_portfolios(db, user_id=current_user.id)
    return [PortfolioResponse.model_validate(item) for item in portfolios]


@router.post("/", response_model=PortfolioResponse)
async def create_portfolio(
    payload: PortfolioCreateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    _rate_limit: None = Depends(check_tiered_rate_limit),
) -> PortfolioResponse:
    portfolio = await portfolio_service.create_portfolio(
        db,
        user_id=current_user.id,
        name=payload.name,
        description=payload.description,
        portfolio_type=payload.portfolio_type,
        base_currency=payload.base_currency,
    )
    return PortfolioResponse.model_validate(portfolio)


@router.get("/id/{portfolio_id}", response_model=PortfolioResponse)
async def get_portfolio(
    portfolio_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    _rate_limit: None = Depends(check_tiered_rate_limit),
) -> PortfolioResponse:
    portfolio = await portfolio_service.get_portfolio(db, portfolio_id=portfolio_id, user_id=current_user.id)
    if portfolio is None:
        raise HTTPException(status_code=404, detail="Portfolio not found")
    return PortfolioResponse.model_validate(portfolio)


@router.post("/id/{portfolio_id}/transactions", response_model=PortfolioTransactionResponse)
async def add_portfolio_transaction(
    portfolio_id: int,
    payload: PortfolioTransactionCreateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    _rate_limit: None = Depends(check_tiered_rate_limit),
) -> PortfolioTransactionResponse:
    portfolio = await portfolio_service.get_portfolio(db, portfolio_id=portfolio_id, user_id=current_user.id)
    if portfolio is None:
        raise HTTPException(status_code=404, detail="Portfolio not found")

    result = await portfolio_service.add_transaction(
        db,
        portfolio_id=portfolio_id,
        transaction_type=payload.transaction_type,
        symbol=payload.symbol,
        quantity=payload.quantity,
        price=payload.price,
        transaction_date=payload.transaction_date,
        fees=payload.fees,
        notes=payload.notes,
    )
    return PortfolioTransactionResponse.model_validate(result["transaction"])


@router.get("/id/{portfolio_id}/analytics", response_model=PortfolioAnalyticsResponse)
async def get_portfolio_analytics(
    portfolio_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    _rate_limit: None = Depends(check_tiered_rate_limit),
) -> PortfolioAnalyticsResponse:
    portfolio = await portfolio_service.get_portfolio(db, portfolio_id=portfolio_id, user_id=current_user.id)
    if portfolio is None:
        raise HTTPException(status_code=404, detail="Portfolio not found")
    data = await portfolio_service.get_portfolio_analytics(db, portfolio_id=portfolio_id)
    return PortfolioAnalyticsResponse.model_validate(data)


@router.get("/watchlists", response_model=list[WatchlistResponse])
async def list_watchlists(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    _rate_limit: None = Depends(check_tiered_rate_limit),
) -> list[WatchlistResponse]:
    watchlists = await portfolio_service.list_watchlists(db, user_id=current_user.id)
    return [WatchlistResponse.model_validate(item) for item in watchlists]


@router.post("/watchlists", response_model=WatchlistResponse)
async def create_watchlist(
    payload: WatchlistCreateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    _rate_limit: None = Depends(check_tiered_rate_limit),
) -> WatchlistResponse:
    watchlist = await portfolio_service.create_watchlist(
        db,
        user_id=current_user.id,
        name=payload.name,
        description=payload.description,
        alert_on_change=payload.alert_on_change,
        change_threshold_percent=payload.change_threshold_percent,
    )
    return WatchlistResponse.model_validate(watchlist)


@router.post("/watchlists/{watchlist_id}/items", response_model=WatchlistItemResponse)
async def add_watchlist_item(
    watchlist_id: int,
    payload: WatchlistItemCreateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    _rate_limit: None = Depends(check_tiered_rate_limit),
) -> WatchlistItemResponse:
    watchlists = await portfolio_service.list_watchlists(db, user_id=current_user.id)
    if not any(item.id == watchlist_id for item in watchlists):
        raise HTTPException(status_code=404, detail="Watchlist not found")

    item = await portfolio_service.add_watchlist_item(
        db,
        watchlist_id=watchlist_id,
        symbol=payload.symbol,
        asset_type=payload.asset_type,
        asset_name=payload.asset_name,
        target_buy_price=payload.target_buy_price,
        target_sell_price=payload.target_sell_price,
        notes=payload.notes,
        tags=payload.tags,
    )
    return WatchlistItemResponse.model_validate(item)


@router.post("/score/{symbol}", response_model=InvestmentScoreResponse)
async def score_investment(
    symbol: str,
    payload: InvestmentScoreRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    _rate_limit: None = Depends(check_tiered_rate_limit),
) -> InvestmentScoreResponse:
    result = await investment_scoring.score_investment(
        db,
        symbol=symbol,
        user_risk_profile=payload.risk_profile,
        user_id=current_user.id,
    )
    return InvestmentScoreResponse.model_validate(result)
