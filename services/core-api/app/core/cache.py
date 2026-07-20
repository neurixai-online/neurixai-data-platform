import json
from collections.abc import AsyncIterator
from typing import Any

from redis.asyncio import Redis, from_url

from neurix_shared.config import settings

_redis: Redis = from_url(settings.redis_url, decode_responses=True)


async def get_redis() -> AsyncIterator[Redis]:
    yield _redis


class CacheRepository:
    """Thin cache-aside helper. Callers own the TTL — see api_products.cache_ttl_seconds
    per dataset once the Product Catalog sync exists; hardcoded here for Milestone 0."""

    def __init__(self, redis: Redis):
        self._redis = redis

    async def get_json(self, key: str) -> Any | None:
        raw = await self._redis.get(key)
        return json.loads(raw) if raw is not None else None

    async def set_json(self, key: str, value: Any, ttl_seconds: int) -> None:
        await self._redis.set(key, json.dumps(value), ex=ttl_seconds)
