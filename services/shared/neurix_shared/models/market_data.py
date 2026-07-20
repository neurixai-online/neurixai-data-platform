from datetime import date as date_
from datetime import datetime as datetime_

from sqlalchemy import Date, DateTime, Float, Integer, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from neurix_shared.db import Base


class ExchangeRate(Base):
    """One row per (currency, rate_date) — upserted, same reasoning as WeatherForecast:
    BOT can revise a published day's rate, so overwriting on re-fetch is correct, not a
    bug. Fetched as a 19-currency batch per day (BOT's own API returns all currencies
    for a date range in one call — no need to loop per currency like weather/province)."""

    __tablename__ = "exchange_rates"
    __table_args__ = (UniqueConstraint("currency_code", "rate_date", name="uq_exchange_rates_currency_date"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    currency_code: Mapped[str] = mapped_column(String(3), nullable=False)
    currency_name_th: Mapped[str] = mapped_column(String(200), nullable=False)
    currency_name_en: Mapped[str] = mapped_column(String(200), nullable=False)
    rate_date: Mapped[date_] = mapped_column(Date, nullable=False)
    buying_sight: Mapped[float | None] = mapped_column(Float, nullable=True)
    buying_transfer: Mapped[float | None] = mapped_column(Float, nullable=True)
    selling: Mapped[float | None] = mapped_column(Float, nullable=True)
    mid_rate: Mapped[float | None] = mapped_column(Float, nullable=True)
    ingested_at: Mapped[datetime_] = mapped_column(DateTime(timezone=True), server_default=func.now())
