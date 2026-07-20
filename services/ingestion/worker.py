import asyncio
import logging
import sys

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from connectors.base import Connector
from connectors.pm25 import Pm25Connector
from connectors.province_district_subdistrict import ProvinceDistrictSubdistrictConnector
from connectors.public_holidays import PublicHolidaysConnector
from neurix_shared.db import async_session_factory

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger("neurix.ingestion.worker")

# Registered by hand for now. Once the API Product Catalog exists, this list is replaced
# by a query against the `connectors` table instead of a literal.
CONNECTORS: list[Connector] = [
    ProvinceDistrictSubdistrictConnector(),
    PublicHolidaysConnector(),
    Pm25Connector(),
]


async def run_once(connector: Connector) -> None:
    async with async_session_factory() as session:
        try:
            await connector.run(session)
        except Exception:
            await session.rollback()
            logger.exception("connector.failed source=%s", connector.source_name)
            raise


async def run_all_once() -> None:
    for connector in CONNECTORS:
        await run_once(connector)


async def _run_scheduler_forever() -> None:
    # AsyncIOScheduler.start() requires a running event loop — it must be called from
    # inside a coroutine driven by asyncio.run(), not before one exists. Blocking on
    # asyncio.Event().wait() (rather than the old loop.run_forever() pattern) is what
    # keeps that same loop alive without fighting asyncio.run()'s own loop management.
    scheduler = AsyncIOScheduler()
    for connector in CONNECTORS:
        scheduler.add_job(
            run_once,
            trigger=CronTrigger.from_crontab(connector.schedule_cron),
            args=[connector],
            id=connector.source_name,
            misfire_grace_time=3600,
        )
        logger.info("scheduled source=%s cron=%s", connector.source_name, connector.schedule_cron)

    scheduler.start()
    logger.info("worker started, waiting for scheduled runs")
    await asyncio.Event().wait()


def main() -> None:
    if "--once" in sys.argv:
        asyncio.run(run_all_once())
        return

    try:
        asyncio.run(_run_scheduler_forever())
    except (KeyboardInterrupt, SystemExit):
        pass


if __name__ == "__main__":
    main()
