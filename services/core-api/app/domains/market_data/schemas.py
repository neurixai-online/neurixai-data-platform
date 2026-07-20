from datetime import date

from pydantic import BaseModel, ConfigDict


class ExchangeRateOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    currency_code: str
    currency_name_th: str
    currency_name_en: str
    rate_date: date
    buying_sight: float | None
    buying_transfer: float | None
    selling: float | None
    mid_rate: float | None
