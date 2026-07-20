from datetime import datetime

from pydantic import BaseModel, ConfigDict


class Pm25ReadingOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    station_id: str
    station_name_th: str
    station_name_en: str
    lat: float
    lon: float
    observed_at: datetime
    pm25_value: float | None
    pm25_aqi: int | None
    color_id: int | None
