from datetime import datetime
from zoneinfo import ZoneInfo

import httpx
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from connectors.base import Connector
from neurix_shared.models import Pm25Reading

_URL = "https://air4thai.pcd.go.th/services/getNewAQI_JSON.php"
_BANGKOK = ZoneInfo("Asia/Bangkok")


def _int_or_none(raw: str) -> int | None:
    value = int(raw)
    return None if value == -1 else value


def _float_or_none(raw: str) -> float | None:
    value = float(raw)
    return None if value == -1 else value


class Pm25Connector(Connector):
    """Source: Air4Thai (air4thai.pcd.go.th), the Pollution Control Department's own
    real-time station network — free, no registration, verified reachable and
    schema-checked 2026-07-20 (~130+ stations nationwide).

    Unlike BOT exchange rates or TMD weather, this endpoint needs no API key, so it's
    the environmental connector built first — those two need a developer account
    registered on their respective portals before a connector for them can be written
    and verified against real credentials."""

    source_name = "th_pm25_air4thai"
    schedule_cron = "0 * * * *"  # hourly — matches the station network's own update cadence

    async def fetch(self) -> dict:
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.get(_URL)
        resp.raise_for_status()
        return resp.json()

    async def transform(self, raw: dict) -> list[dict]:
        records = []
        for station in raw["stations"]:
            last = station.get("AQILast")
            if not last or not last.get("date") or not last.get("time"):
                continue  # station reporting nothing usable this run — skip, don't fabricate a row

            observed_at = datetime.strptime(f"{last['date']} {last['time']}", "%Y-%m-%d %H:%M").replace(
                tzinfo=_BANGKOK
            )
            pm25 = last.get("PM25", {})
            records.append(
                {
                    "station_id": station["stationID"],
                    "station_name_th": station["nameTH"],
                    "station_name_en": station["nameEN"],
                    "lat": float(station["lat"]),
                    "lon": float(station["long"]),
                    "observed_at": observed_at,
                    "pm25_value": _float_or_none(pm25.get("value", "-1")),
                    "pm25_aqi": _int_or_none(pm25.get("aqi", "-1")),
                    "color_id": _int_or_none(pm25.get("color_id", "-1")),
                }
            )
        return records

    async def load(self, session: AsyncSession, records: list[dict]) -> int:
        if not records:
            return 0
        stmt = pg_insert(Pm25Reading).values(records)
        stmt = stmt.on_conflict_do_update(
            index_elements=[Pm25Reading.station_id, Pm25Reading.observed_at],
            set_={
                "station_name_th": stmt.excluded.station_name_th,
                "station_name_en": stmt.excluded.station_name_en,
                "lat": stmt.excluded.lat,
                "lon": stmt.excluded.lon,
                "pm25_value": stmt.excluded.pm25_value,
                "pm25_aqi": stmt.excluded.pm25_aqi,
                "color_id": stmt.excluded.color_id,
            },
        )
        await session.execute(stmt)
        return len(records)
