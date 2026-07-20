from datetime import datetime as datetime_

from sqlalchemy import DateTime, Float, Integer, String, UniqueConstraint, func
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
