from datetime import date, timedelta

import httpx
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from connectors.base import Connector
from neurix_shared.config import settings
from neurix_shared.models import ExchangeRate

_URL = "https://gateway.api.bot.or.th/Stat-ExchangeRate/v2/DAILY_AVG_EXG_RATE/"
_WINDOW_DAYS = 30  # rolling window — re-fetches recent days (BOT can revise a published
# rate) without unbounded per-run growth; older days already in the DB are left alone.


class ExchangeRateConnector(Connector):
    """Source: Bank of Thailand's official API (portal.api.bot.or.th, "Exchange Rates"
    product) — Daily Weighted-average Interbank Exchange Rate, THB vs 19 currencies.
    Requires a subscription key registered by a human on the BOT developer portal
    (`BOT_API_TOKEN`); verified reachable and schema-checked live 2026-07-20.

    Auth is the one surprise here: BOT's gateway takes the raw subscription key as the
    literal `Authorization` header value — no "Bearer " prefix, unlike TMD/most APIs.
    Confirmed from BOT's own interactive docs sample, not assumed.

    One HTTP call covers all 19 currencies for the whole date range (unlike weather,
    which needs one call per province) — omitting the `currency` query param returns
    every currency BOT publishes."""

    source_name = "th_exchange_rate_bot"
    schedule_cron = "0 19 * * *"  # daily, after BOT's own 18:00 (BKK) release schedule

    async def fetch(self, session: AsyncSession) -> list[dict]:
        end = date.today()
        start = end - timedelta(days=_WINDOW_DAYS)
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.get(
                _URL,
                params={"start_period": start.isoformat(), "end_period": end.isoformat()},
                headers={"Accept": "*/*", "Authorization": settings.bot_api_token},
            )
        resp.raise_for_status()
        return resp.json()["result"]["data"]["data_detail"]

    async def transform(self, raw: list[dict]) -> list[dict]:
        def to_float(value: str | None) -> float | None:
            return float(value) if value not in (None, "") else None

        return [
            {
                "currency_code": row["currency_id"],
                "currency_name_th": row["currency_name_th"],
                "currency_name_en": row["currency_name_eng"].strip(),
                "rate_date": date.fromisoformat(row["period"]),
                "buying_sight": to_float(row.get("buying_sight")),
                "buying_transfer": to_float(row.get("buying_transfer")),
                "selling": to_float(row.get("selling")),
                "mid_rate": to_float(row.get("mid_rate")),
            }
            for row in raw
        ]

    async def load(self, session: AsyncSession, records: list[dict]) -> int:
        if not records:
            return 0
        stmt = pg_insert(ExchangeRate).values(records)
        stmt = stmt.on_conflict_do_update(
            index_elements=[ExchangeRate.currency_code, ExchangeRate.rate_date],
            set_={
                "currency_name_th": stmt.excluded.currency_name_th,
                "currency_name_en": stmt.excluded.currency_name_en,
                "buying_sight": stmt.excluded.buying_sight,
                "buying_transfer": stmt.excluded.buying_transfer,
                "selling": stmt.excluded.selling,
                "mid_rate": stmt.excluded.mid_rate,
            },
        )
        await session.execute(stmt)
        return len(records)
