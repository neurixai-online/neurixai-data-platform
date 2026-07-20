from fastapi import APIRouter, Depends, HTTPException
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.cache import CacheRepository, get_redis
from app.core.db import get_session
from app.domains.reference_data import repository
from app.domains.reference_data.schemas import DistrictOut, HolidayOut, ProvinceOut, SubdistrictOut

router = APIRouter(prefix="/v1/reference", tags=["reference-data"])

# Reference data changes on the order of months, not minutes — a long TTL is deliberate,
# not an oversight. Once the API Product Catalog exists this comes from api_products.cache_ttl_seconds
# per dataset instead of being hardcoded per endpoint.
_CACHE_TTL_SECONDS = 6 * 60 * 60


@router.get("/provinces", response_model=list[ProvinceOut])
async def get_provinces(
    session: AsyncSession = Depends(get_session),
    redis: Redis = Depends(get_redis),
) -> list[dict]:
    cache = CacheRepository(redis)
    cache_key = "ref:provinces"

    cached = await cache.get_json(cache_key)
    if cached is not None:
        return cached

    rows = await repository.list_provinces(session)
    await cache.set_json(cache_key, rows, _CACHE_TTL_SECONDS)
    return rows


@router.get("/districts", response_model=list[DistrictOut])
async def get_districts(
    province_code: int,
    session: AsyncSession = Depends(get_session),
    redis: Redis = Depends(get_redis),
) -> list[dict]:
    cache = CacheRepository(redis)
    cache_key = f"ref:districts:{province_code}"

    cached = await cache.get_json(cache_key)
    if cached is not None:
        return cached

    rows = await repository.list_districts(session, province_code)
    if not rows:
        raise HTTPException(status_code=404, detail=f"No districts found for province_code={province_code}")

    await cache.set_json(cache_key, rows, _CACHE_TTL_SECONDS)
    return rows


@router.get("/holidays", response_model=list[HolidayOut])
async def get_holidays(
    year: int | None = None,
    session: AsyncSession = Depends(get_session),
    redis: Redis = Depends(get_redis),
) -> list[dict]:
    cache = CacheRepository(redis)
    cache_key = f"ref:holidays:{year if year is not None else 'all'}"

    cached = await cache.get_json(cache_key)
    if cached is not None:
        return cached

    rows = await repository.list_holidays(session, year)
    await cache.set_json(cache_key, rows, _CACHE_TTL_SECONDS)
    return rows


@router.get("/subdistricts", response_model=list[SubdistrictOut])
async def get_subdistricts(
    district_code: int,
    session: AsyncSession = Depends(get_session),
    redis: Redis = Depends(get_redis),
) -> list[dict]:
    cache = CacheRepository(redis)
    cache_key = f"ref:subdistricts:{district_code}"

    cached = await cache.get_json(cache_key)
    if cached is not None:
        return cached

    rows = await repository.list_subdistricts(session, district_code)
    if not rows:
        raise HTTPException(status_code=404, detail=f"No subdistricts found for district_code={district_code}")

    await cache.set_json(cache_key, rows, _CACHE_TTL_SECONDS)
    return rows
