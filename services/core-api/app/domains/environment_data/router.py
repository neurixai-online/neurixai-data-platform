from fastapi import APIRouter, Depends
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.cache import CacheRepository, get_redis
from app.core.db import get_session
from app.domains.environment_data import repository
from app.domains.environment_data.schemas import Pm25ReadingOut

router = APIRouter(prefix="/v1/environment", tags=["environment-data"])

# Station network updates hourly — a much shorter TTL than reference data's 6h, since
# stale-by-hours here would misrepresent current air quality, not just an admin boundary.
_CACHE_TTL_SECONDS = 10 * 60


@router.get("/pm25", response_model=list[Pm25ReadingOut])
async def get_pm25(
    station_id: str | None = None,
    session: AsyncSession = Depends(get_session),
    redis: Redis = Depends(get_redis),
) -> list[dict]:
    cache = CacheRepository(redis)
    cache_key = f"env:pm25:{station_id if station_id is not None else 'all'}"

    cached = await cache.get_json(cache_key)
    if cached is not None:
        return cached

    rows = await repository.list_latest_pm25(session, station_id)
    await cache.set_json(cache_key, rows, _CACHE_TTL_SECONDS)
    return rows
