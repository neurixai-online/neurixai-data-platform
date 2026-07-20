from datetime import date

import httpx
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from connectors.base import Connector
from neurix_shared.models import PublicHoliday

_URL_TEMPLATE = "https://tallyfy.com/national-holidays/api/TH/{year}.json"

# Previous + current + next year: enough for "was X a holiday" lookups and forward
# scheduling without unbounded growth. Once the API Product Catalog exists this becomes
# connector config instead of a literal. Not every year in this window is guaranteed to
# exist at the source (see fetch()) — that's expected, not an error.
_YEARS = [date.today().year - 1, date.today().year, date.today().year + 1]


class PublicHolidaysConnector(Connector):
    """Source: tallyfy.com/national-holidays (CC0 / public domain; verified reachable
    and schema-checked 2026-07-20). This is a third-party aggregator, not the Royal
    Gazette itself — the source page's own disclaimer says to verify critical dates
    against official government sources, which is worth surfacing to API consumers too,
    not just noting here.

    Unlike province/district/subdistrict, Thai holiday compensation days can be added by
    a mid-year cabinet resolution, so this runs weekly rather than monthly."""

    source_name = "th_public_holidays"
    schedule_cron = "0 4 * * 1"  # weekly, Monday 04:00

    async def fetch(self, session: AsyncSession) -> list[dict]:
        # Verified live: this source 404s for years outside some window it maintains
        # (e.g. no prior-year archive) rather than always covering [this_year-1, +1] as
        # originally assumed. A missing year is an expected gap in the window, not a
        # transient failure, so it's skipped here rather than failing the whole run —
        # any other status (5xx, network error) still raises and goes through the
        # base class's retry.
        payloads: list[dict] = []
        async with httpx.AsyncClient(timeout=30) as client:
            for year in _YEARS:
                resp = await client.get(_URL_TEMPLATE.format(year=year))
                if resp.status_code == 404:
                    continue
                resp.raise_for_status()
                payloads.append(resp.json())
        return payloads

    async def transform(self, raw: list[dict]) -> list[dict]:
        records = []
        for year_payload in raw:
            for h in year_payload["holidays"]:
                records.append(
                    {
                        # asyncpg's DATE binding needs actual date objects, not ISO
                        # strings — it won't parse them for you.
                        "date": date.fromisoformat(h["date"]),
                        "observed_date": date.fromisoformat(h["observed_date"]),
                        "name_th": h["local_name"],
                        "name_en": h["name"],
                        "is_shifted": h["is_observed_shifted"],
                        "description": h.get("description"),
                    }
                )
        return records

    async def load(self, session: AsyncSession, records: list[dict]) -> int:
        if not records:
            return 0
        stmt = pg_insert(PublicHoliday).values(records)
        stmt = stmt.on_conflict_do_update(
            index_elements=[PublicHoliday.date, PublicHoliday.name_en],
            set_={
                "observed_date": stmt.excluded.observed_date,
                "name_th": stmt.excluded.name_th,
                "is_shifted": stmt.excluded.is_shifted,
                "description": stmt.excluded.description,
            },
        )
        await session.execute(stmt)
        return len(records)
