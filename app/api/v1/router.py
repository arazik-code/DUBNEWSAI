from fastapi import APIRouter

from app.api.v1 import (
    admin,
    alerts,
    analytics,
    auth,
    competitors,
    executive,
    market,
    mobile,
    news,
    notifications,
    portfolios,
    predictions,
    settings,
    subscription,
    teams,
    websocket,
)

api_router = APIRouter()
api_router.include_router(auth.router)
api_router.include_router(news.router)
api_router.include_router(market.router)
api_router.include_router(mobile.router)
api_router.include_router(portfolios.router)
api_router.include_router(competitors.router)
api_router.include_router(predictions.router)
api_router.include_router(executive.router)
api_router.include_router(teams.router)
api_router.include_router(analytics.router)
api_router.include_router(settings.router)
api_router.include_router(subscription.router)
api_router.include_router(alerts.router)
api_router.include_router(notifications.router)
api_router.include_router(websocket.router)
api_router.include_router(admin.router)
