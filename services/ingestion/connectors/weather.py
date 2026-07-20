import asyncio
from datetime import datetime as dt

import httpx
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from connectors.base import Connector
from neurix_shared.config import settings
from neurix_shared.models import Province, WeatherForecast

_URL = "https://data.tmd.go.th/nwpapi/v1/forecast/location/daily/place"
_FIELDS = "cond,rh,tc_max,tc_min,rain"
_DURATION_DAYS = 7


class WeatherConnector(Connector):
    """Source: Thai Meteorological Department's nwpapi (data.tmd.go.th/nwpapi), a
    Bearer-token API requiring registration at data.tmd.go.th/nwpapi/register — verified
    reachable and schema-checked 2026-07-20 with a real token (`TMD_API_TOKEN` env var,
    valid ~1 year from issuance per its JWT `exp` claim).

    Queried per-province by Thai name (one HTTP call each) rather than by lat/lon, since
    we already have the canonical province list from the reference_data connector — this
    is the one connector so far whose fetch() needs to read the DB first, which is why
    Connector.fetch() takes `session`. `geocode` in TMD's response matches our own
    `provinces.code` exactly (verified against live data), used as the soft join key.

    77 sequential requests per run, not concurrent. This is genuinely rate-limited, not
    just "being courteous" — confirmed live via response headers: `x-ratelimit-limit: 60`
    or requests in whatever their window is, with `Retry-After` on a 429. 77 provinces
    exceeds that in one run, so hitting 429 partway through is the expected steady state,
    not a rare edge case — each request honors Retry-After individually rather than
    letting the whole batch fail and restart from province #1 (which was the original,
    wrong assumption here: restarting from scratch just re-triggers the same limit
    immediately, confirmed by an actual failed run)."""

    source_name = "th_weather_tmd"
    schedule_cron = "0 */6 * * *"  # every 6 hours — matches TMD's own NWP model rerun cadence, not just a guess at "often enough"
    _MAX_RATE_LIMIT_RETRIES = 5

    async def _get_with_rate_limit_retry(self, client: httpx.AsyncClient, name_th: str) -> httpx.Response:
        for attempt in range(self._MAX_RATE_LIMIT_RETRIES):
            resp = await client.get(
                _URL,
                params={"province": name_th, "duration": _DURATION_DAYS, "fields": _FIELDS},
                headers={"authorization": f"Bearer {settings.tmd_api_token}"},
            )
            if resp.status_code != 429:
                resp.raise_for_status()
                return resp
            wait_seconds = int(resp.headers.get("Retry-After", "15"))
            await asyncio.sleep(wait_seconds)
        # Exhausted retries — raise the last 429 so the base class's own retry/logging takes over.
        resp.raise_for_status()
        return resp

    async def fetch(self, session: AsyncSession) -> list[tuple[int, dict]]:
        provinces = (await session.execute(select(Province.code, Province.name_th))).all()

        results: list[tuple[int, dict]] = []
        async with httpx.AsyncClient(timeout=30) as client:
            for code, name_th in provinces:
                resp = await self._get_with_rate_limit_retry(client, name_th)
                results.append((code, resp.json()))
        return results

    async def transform(self, raw: list[tuple[int, dict]]) -> list[dict]:
        records = []
        for province_code, payload in raw:
            forecasts = payload.get("WeatherForecasts") or []
            if not forecasts:
                continue
            location = forecasts[0]["location"]
            for entry in forecasts[0]["forecasts"]:
                forecast_date = dt.fromisoformat(entry["time"]).date()
                data = entry["data"]
                records.append(
                    {
                        "province_code": province_code,
                        "province_name_th": location["name"],
                        "forecast_date": forecast_date,
                        "cond": data.get("cond"),
                        "tc_max": data.get("tc_max"),
                        "tc_min": data.get("tc_min"),
                        "rh": data.get("rh"),
                        "rain": data.get("rain"),
                    }
                )
        return records

    async def load(self, session: AsyncSession, records: list[dict]) -> int:
        if not records:
            return 0
        stmt = pg_insert(WeatherForecast).values(records)
        stmt = stmt.on_conflict_do_update(
            index_elements=[WeatherForecast.province_code, WeatherForecast.forecast_date],
            set_={
                "province_name_th": stmt.excluded.province_name_th,
                "cond": stmt.excluded.cond,
                "tc_max": stmt.excluded.tc_max,
                "tc_min": stmt.excluded.tc_min,
                "rh": stmt.excluded.rh,
                "rain": stmt.excluded.rain,
            },
        )
        await session.execute(stmt)
        return len(records)
