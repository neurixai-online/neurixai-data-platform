from datetime import date

from fastapi import APIRouter, Depends
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.cache import CacheRepository, get_redis
from app.core.db import get_session
from app.domains.market_data import repository
from app.domains.market_data.schemas import ExchangeRateOut

router = APIRouter(prefix="/v1/market", tags=["market-data"])

# Connector runs once daily — cache well under that so we're never serving a rate more
# than a few hours stale relative to when the connector last actually ran.
_CACHE_TTL_SECONDS = 3 * 60 * 60


@router.get("/exchange-rates", response_model=list[ExchangeRateOut])
async def get_exchange_rates(
    currency_code: str | None = None,
    start_date: date | None = None,
    end_date: date | None = None,
    session: AsyncSession = Depends(get_session),
    redis: Redis = Depends(get_redis),
) -> list[dict]:
    cache = CacheRepository(redis)
    cache_key = f"market:exchange-rates:{currency_code or 'all'}:{start_date or ''}:{end_date or ''}"

    cached = await cache.get_json(cache_key)
    if cached is not None:
        return cached

    rows = await repository.list_exchange_rates(session, currency_code, start_date, end_date)
    await cache.set_json(cache_key, rows, _CACHE_TTL_SECONDS)
    return rows
