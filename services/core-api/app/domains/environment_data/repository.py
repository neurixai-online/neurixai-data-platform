from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from neurix_shared.models import Pm25Reading, WeatherForecast


async def list_latest_pm25(session: AsyncSession, station_id: str | None) -> list[dict]:
    # DISTINCT ON (Postgres-specific, fine — this whole stack is Postgres-tied already)
    # picks the newest row per station in one query instead of a correlated subquery.
    stmt = (
        select(
            Pm25Reading.station_id,
            Pm25Reading.station_name_th,
            Pm25Reading.station_name_en,
            Pm25Reading.lat,
            Pm25Reading.lon,
            Pm25Reading.observed_at,
            Pm25Reading.pm25_value,
            Pm25Reading.pm25_aqi,
            Pm25Reading.color_id,
        )
        .distinct(Pm25Reading.station_id)
        .order_by(Pm25Reading.station_id, Pm25Reading.observed_at.desc())
    )
    if station_id is not None:
        stmt = stmt.where(Pm25Reading.station_id == station_id)

    result = await session.execute(stmt)
    # observed_at is a Python datetime — not JSON-serializable as-is, and this dict is
    # what gets cached (see CacheRepository.set_json), so convert to an ISO string now.
    return [{**dict(row), "observed_at": row["observed_at"].isoformat()} for row in result.mappings().all()]


async def list_weather_forecasts(session: AsyncSession, province_code: int | None) -> list[dict]:
    stmt = select(
        WeatherForecast.province_code,
        WeatherForecast.province_name_th,
        WeatherForecast.forecast_date,
        WeatherForecast.cond,
        WeatherForecast.tc_max,
        WeatherForecast.tc_min,
        WeatherForecast.rh,
        WeatherForecast.rain,
    ).order_by(WeatherForecast.province_code, WeatherForecast.forecast_date)
    if province_code is not None:
        stmt = stmt.where(WeatherForecast.province_code == province_code)

    result = await session.execute(stmt)
    # forecast_date is a Python date — same JSON-serializability issue as observed_at above.
    return [{**dict(row), "forecast_date": row["forecast_date"].isoformat()} for row in result.mappings().all()]
