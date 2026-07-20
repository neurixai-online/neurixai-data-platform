import logging
from abc import ABC, abstractmethod
from typing import Any

import httpx
from sqlalchemy.ext.asyncio import AsyncSession
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential_jitter

logger = logging.getLogger("neurix.ingestion")


class Connector(ABC):
    """Base interface every data source adapter implements. Adding a new dataset in a
    later phase means subclassing this and registering a row in the `connectors` table —
    the worker, scheduler, and DB session handling never change."""

    source_name: str
    schedule_cron: str

    @abstractmethod
    async def fetch(self) -> Any:
        """Pull the raw payload from the external source. Network I/O only — no shaping."""

    @abstractmethod
    async def transform(self, raw: Any) -> Any:
        """Rename/reshape the raw payload into records keyed the way our schema expects.
        Pure function — no DB access here, so it stays unit-testable without a database."""

    @abstractmethod
    async def load(self, session: AsyncSession, records: Any) -> int:
        """Upsert records (idempotent — safe to re-run after a crash or a manual retry
        with no side effects beyond the intended write). Returns rows affected."""

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential_jitter(initial=1, max=20),
        retry=retry_if_exception_type(httpx.HTTPError),
        reraise=True,
    )
    async def _fetch_with_retry(self) -> Any:
        # Only network/HTTP errors are retried — a bug inside fetch() (e.g. a bad URL
        # constant) should fail fast on the first attempt, not retry 3 times masking it.
        return await self.fetch()

    async def run(self, session: AsyncSession) -> None:
        logger.info("connector.start source=%s", self.source_name)
        raw = await self._fetch_with_retry()
        records = await self.transform(raw)
        affected = await self.load(session, records)
        await session.commit()
        logger.info("connector.done source=%s affected=%s", self.source_name, affected)
