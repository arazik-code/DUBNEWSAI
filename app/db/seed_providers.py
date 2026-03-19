from sqlalchemy.ext.asyncio import AsyncSession

from app.services.provider_observability_service import ProviderObservabilityService


async def seed_providers(db: AsyncSession) -> int:
    providers = await ProviderObservabilityService.sync_registry_to_db(db)
    await db.commit()
    return len(providers)
