import asyncio
from contextlib import asynccontextmanager, suppress

from fastapi import Depends, FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, Response
from prometheus_client import generate_latest
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.router import api_router
from app.config import get_settings
from app.core.cache import cache
from app.core.compression import SmartCompressionMiddleware
from app.core.database_optimizer import DatabaseOptimizer
from app.core.error_handler import (
    database_exception_handler,
    global_exception_handler,
    validation_exception_handler,
)
from app.core.exceptions import AppException
from app.core.logging import logger, setup_logging
from app.core.metrics import MetricsCollector, metrics_middleware
from app.core.middleware import OptionalAuthMiddleware, RequestContextMiddleware, SecurityHeadersMiddleware
from app.core.monitoring import BetterStackMonitor
from app.core.redis_publisher import redis_publisher
from app.core.rate_limit import limiter
from app.database import engine, get_db
from app.services.embedded_sync_service import EmbeddedSyncService

settings = get_settings()
setup_logging()
DatabaseOptimizer.setup_query_logging()


@asynccontextmanager
async def lifespan(_: FastAPI):
    logger.info("Starting DUBNEWSAI backend")
    async with engine.begin() as connection:
        await connection.execute(text("SELECT 1"))
    await cache.connect()
    await redis_publisher.connect()
    metrics_task = asyncio.create_task(MetricsCollector.collect_system_metrics())
    embedded_sync_task: asyncio.Task[None] | None = None
    if settings.embedded_sync_enabled:
        await EmbeddedSyncService.bootstrap_news_if_empty()
        embedded_sync_task = asyncio.create_task(EmbeddedSyncService.run_news_sync_loop())
    await BetterStackMonitor.send_heartbeat(settings.BETTERSTACK_HEARTBEAT_CHECK_ID)
    logger.info("Application started")
    yield
    metrics_task.cancel()
    with suppress(asyncio.CancelledError):
        await metrics_task
    await EmbeddedSyncService.shutdown_task(embedded_sync_task)
    await cache.disconnect()
    await redis_publisher.disconnect()
    await engine.dispose()
    logger.info("Application shutdown")
    logger.info("Stopped DUBNEWSAI backend")


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan,
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(SQLAlchemyError, database_exception_handler)
app.middleware("http")(metrics_middleware)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(SmartCompressionMiddleware)
app.add_middleware(RequestContextMiddleware)
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(OptionalAuthMiddleware)
app.add_middleware(SlowAPIMiddleware)

app.include_router(api_router, prefix=settings.API_V1_PREFIX)


@app.get("/health")
@limiter.limit("100/minute")
async def health_check(request: Request, db: AsyncSession = Depends(get_db)):
    del request
    await db.execute(text("SELECT 1"))
    return {"status": "healthy", "version": settings.APP_VERSION}


@app.get("/metrics")
async def metrics() -> Response:
    return Response(content=generate_latest(), media_type="text/plain")


@app.exception_handler(AppException)
async def app_exception_handler(_: Request, exc: AppException) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail, "error_code": exc.error_code},
    )


app.add_exception_handler(Exception, global_exception_handler)
