from __future__ import annotations

import asyncio

from celery import shared_task
from loguru import logger

from app.database import AsyncSessionLocal
from app.services.predictive import forecast_service


TOP_SYMBOLS = ["EMAAR.DU", "DAMAC.DU", "ALDAR.AD", "DFM.DU"]


@shared_task(name="daily_prediction_update")
def daily_prediction_update() -> None:
    asyncio.run(_daily_prediction_update())


async def _daily_prediction_update() -> None:
    forecast_service.clear_cache()
    async with AsyncSessionLocal() as db:
        for symbol in TOP_SYMBOLS:
            try:
                await forecast_service.predict_price_movement(db, symbol=symbol, days_ahead=30, use_cache=False)
            except Exception as exc:
                logger.error("Prediction prewarm failed for {}: {}", symbol, str(exc))
