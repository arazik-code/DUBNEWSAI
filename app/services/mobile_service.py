from __future__ import annotations

from typing import Any

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.models.market_data import MarketType
from app.models.notification import Notification
from app.models.user import User
from app.schemas.market_data import MarketDataResponse, WeatherSnapshotResponse
from app.schemas.mobile import (
    MobileAlertsSnapshot,
    MobileArticleCard,
    MobileBootstrapResponse,
    MobileCompetitorSpotlight,
    MobileFeatureAccessCard,
    MobileMarketCard,
    MobileMarketPulse,
    MobileNotificationCard,
    MobileNotificationsSnapshot,
    MobilePortfolioHoldingCard,
    MobilePortfolioSnapshot,
    MobileWorkspaceSummary,
)
from app.schemas.news import NewsArticleResponse
from app.schemas.user import UserResponse
from app.services.alert_service import AlertService
from app.services.collaboration.team_service import team_service
from app.services.competitive_intelligence import competitor_service
from app.services.feature_access_service import feature_access_service
from app.services.market_service import MarketService
from app.services.news_service import NewsService
from app.services.notification_service import NotificationService
from app.services.portfolio.portfolio_service import portfolio_service
from app.services.predictive import forecast_service
from app.services.intelligence.property_valuation_service import property_valuation

settings = get_settings()


class MobileAppService:
    def _serialize_article_card(self, payload: Any) -> MobileArticleCard:
        article = NewsArticleResponse.model_validate(payload)
        return MobileArticleCard(
            id=article.id,
            title=article.title,
            description=article.description,
            source_name=article.source_name,
            category=article.category.value if hasattr(article.category, "value") else str(article.category),
            sentiment=article.sentiment.value if hasattr(article.sentiment, "value") else str(article.sentiment),
            published_at=article.published_at,
            image_url=article.image_url,
            relevance_score=article.relevance_score,
        )

    def _serialize_market_card(self, payload: Any) -> MobileMarketCard:
        item = MarketDataResponse.model_validate(payload)
        exchange = item.exchange.value if hasattr(item.exchange, "value") else (str(item.exchange) if item.exchange else None)
        market_type = item.market_type.value if hasattr(item.market_type, "value") else str(item.market_type)
        return MobileMarketCard(
            symbol=item.symbol,
            name=item.name,
            price=item.price,
            change_percent=item.change_percent,
            currency=item.currency,
            exchange=exchange,
            market_type=market_type,
        )

    async def build_bootstrap(
        self,
        db: AsyncSession,
        *,
        user: User | None,
    ) -> MobileBootstrapResponse:
        feature_access = await feature_access_service.get_user_feature_access(db, user=user)
        featured_articles = await NewsService.get_featured_articles(db, limit=4)
        trending_articles = await NewsService.get_trending_articles(db, limit=6)
        movers = await MarketService.get_latest_market_data(db, MarketType.STOCK, limit=6)
        real_estate_leaders = await MarketService.get_real_estate_companies(db)
        weather = await MarketService.get_market_weather()
        trend_prediction = await forecast_service.predict_market_trend(db, region="UAE")
        prediction_universe = await forecast_service.get_prediction_universe(db)
        property_options = await property_valuation.get_property_options(db)

        workspace_summary = None
        if user is not None:
            workspace_summary = await self.build_workspace_summary(
                db,
                user=user,
                feature_access=feature_access,
            )

        return MobileBootstrapResponse(
            app_name=settings.APP_NAME,
            app_version=settings.APP_VERSION,
            feature_access=[
                MobileFeatureAccessCard(
                    feature_key=item["feature_key"],
                    label=item["label"],
                    description=item.get("description"),
                    category=item["category"],
                    has_access=bool(item["has_access"]),
                    public_access=bool(item["public_access"]),
                    grantable=bool(item["grantable"]),
                )
                for item in feature_access
                if item["feature_key"] != "admin_providers"
            ],
            hero_article=self._serialize_article_card(featured_articles[0]) if featured_articles else None,
            featured_articles=[self._serialize_article_card(item) for item in featured_articles],
            trending_articles=[self._serialize_article_card(item) for item in trending_articles],
            market_pulse=MobileMarketPulse(
                market_status=trend_prediction.get("market_status") if isinstance(trend_prediction, dict) else None,
                movers=[self._serialize_market_card(item) for item in movers[:6]],
                real_estate_leaders=[self._serialize_market_card(item) for item in real_estate_leaders[:4]],
                weather=WeatherSnapshotResponse.model_validate(weather) if weather else None,
                trend_prediction=trend_prediction,
            ),
            prediction_universe=prediction_universe,
            property_options=property_options,
            workspace_summary=workspace_summary,
        )

    async def build_workspace_summary(
        self,
        db: AsyncSession,
        *,
        user: User,
        feature_access: list[dict] | None = None,
    ) -> MobileWorkspaceSummary:
        feature_access = feature_access or await feature_access_service.get_user_feature_access(db, user=user)
        enabled_features = [item["feature_key"] for item in feature_access if item["has_access"]]
        notifications = await NotificationService.get_user_notifications(db, user.id, unread_only=False, limit=8)
        unread_count = await db.scalar(
            select(func.count(Notification.id)).where(
                Notification.user_id == user.id,
                Notification.is_read.is_(False),
            )
        )
        teams = await team_service.list_teams_for_user(db, user_id=user.id) if "teams" in enabled_features else []

        portfolios_snapshot = None
        if "portfolios" in enabled_features:
            portfolios = await portfolio_service.list_portfolios(db, user_id=user.id)
            watchlists = await portfolio_service.list_watchlists(db, user_id=user.id)
            top_holdings: list[MobilePortfolioHoldingCard] = []
            all_holdings = []
            for portfolio in portfolios:
                all_holdings.extend(portfolio.holdings or [])
            all_holdings.sort(key=lambda item: item.current_value or 0.0, reverse=True)
            for holding in all_holdings[:4]:
                top_holdings.append(
                    MobilePortfolioHoldingCard(
                        symbol=holding.symbol,
                        asset_name=holding.asset_name,
                        current_value=float(holding.current_value or 0.0),
                        return_percent=float(holding.unrealized_gain_loss_percent or 0.0),
                    )
                )

            total_value = sum(float(item.total_value_aed or 0.0) for item in portfolios)
            return_basis = sum(float(item.total_cost_aed or 0.0) for item in portfolios)
            total_return_percent = ((total_value - return_basis) / return_basis * 100) if return_basis else 0.0
            portfolios_snapshot = MobilePortfolioSnapshot(
                portfolio_count=len(portfolios),
                watchlist_count=len(watchlists),
                total_value_aed=round(total_value, 2),
                total_return_percent=round(total_return_percent, 2),
                watch_items=sum(len(item.items or []) for item in watchlists),
                top_holdings=top_holdings,
            )

        alerts_snapshot = None
        if "alerts" in enabled_features:
            alert_intelligence = await AlertService.get_alert_intelligence(db, user.id)
            alerts_snapshot = MobileAlertsSnapshot(
                summary=alert_intelligence["summary"],
                recent_triggers=alert_intelligence["recent_triggers"],
                templates=alert_intelligence["templates"],
            )

        competitor_spotlight = None
        if "competitors" in enabled_features:
            competitors = await competitor_service.list_competitors(db)
            if competitors:
                lead = competitors[0]
                analysis = await competitor_service._assess_threat_level(db, lead)
                competitor_spotlight = MobileCompetitorSpotlight(
                    id=lead.id,
                    name=lead.name,
                    ticker_symbol=lead.ticker_symbol,
                    market_share_percent=lead.market_share_percent,
                    threat_level=analysis.get("threat_level"),
                    strategic_note=analysis.get("recommended_actions", [None])[0],
                )

        return MobileWorkspaceSummary(
            user=UserResponse.model_validate(user),
            enabled_features=enabled_features,
            portfolios=portfolios_snapshot,
            alerts=alerts_snapshot,
            notifications=MobileNotificationsSnapshot(
                unread_count=int(unread_count or 0),
                latest=[
                    MobileNotificationCard(
                        id=item.id,
                        title=item.title,
                        message=item.message,
                        priority=item.priority.value if hasattr(item.priority, "value") else str(item.priority),
                        created_at=item.created_at,
                        is_read=item.is_read,
                    )
                    for item in notifications
                ],
            ),
            teams_count=len(teams),
            competitor_spotlight=competitor_spotlight,
        )


mobile_app_service = MobileAppService()
