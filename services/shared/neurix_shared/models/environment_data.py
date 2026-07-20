from datetime import date as date_
from datetime import datetime as datetime_

from sqlalchemy import Date, DateTime, Float, Integer, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from neurix_shared.db import Base


class Pm25Reading(Base):
    """One row per station per observed hour — genuine time-series data, not a
    current-state upsert like reference_data. Rows accumulate; revisit partitioning by
    month once volume grows (same deferred concern as usage_logs)."""

    __tablename__ = "pm25_readings"
    __table_args__ = (UniqueConstraint("station_id", "observed_at", name="uq_pm25_readings_station_observed"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    station_id: Mapped[str] = mapped_column(String(20), nullable=False)
    station_name_th: Mapped[str] = mapped_column(String(200), nullable=False)
    station_name_en: Mapped[str] = mapped_column(String(200), nullable=False)
    lat: Mapped[float] = mapped_column(Float, nullable=False)
    lon: Mapped[float] = mapped_column(Float, nullable=False)
    observed_at: Mapped[datetime_] = mapped_column(DateTime(timezone=True), nullable=False)
    # Nullable, not a -1 sentinel — the source uses -1 to mean "sensor has no reading",
    # and propagating that as if it were a real µg/m³ value would be a data-quality bug.
    pm25_value: Mapped[float | None] = mapped_column(Float, nullable=True)
    pm25_aqi: Mapped[int | None] = mapped_column(Integer, nullable=True)
    color_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    ingested_at: Mapped[datetime_] = mapped_column(DateTime(timezone=True), server_default=func.now())


class WeatherForecast(Base):
    """One row per (province, forecast_date) — upserted, not accumulated. Unlike
    pm25_readings this represents "the best current forecast for that date", which gets
    revised as the date approaches, so overwriting is the correct semantic, not a bug.

    province_code deliberately has no FK to provinces.code — same domain-independence
    reasoning as everywhere else in this codebase: environment_data should stay
    extractable into its own service without a hard DB-level dependency on
    reference_data. It's confirmed (2026-07-20) to be the same numbering both datasets
    use (verified against our own `provinces` table), so it's a reliable soft join key."""

    __tablename__ = "weather_forecasts"
    __table_args__ = (UniqueConstraint("province_code", "forecast_date", name="uq_weather_forecasts_province_date"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    province_code: Mapped[int] = mapped_column(Integer, nullable=False)
    province_name_th: Mapped[str] = mapped_column(String(120), nullable=False)
    forecast_date: Mapped[date_] = mapped_column(Date, nullable=False)
    cond: Mapped[int | None] = mapped_column(Integer, nullable=True)  # TMD weather condition code
    tc_max: Mapped[float | None] = mapped_column(Float, nullable=True)
    tc_min: Mapped[float | None] = mapped_column(Float, nullable=True)
    rh: Mapped[float | None] = mapped_column(Float, nullable=True)  # relative humidity %
    rain: Mapped[float | None] = mapped_column(Float, nullable=True)  # mm
    ingested_at: Mapped[datetime_] = mapped_column(DateTime(timezone=True), server_default=func.now())
