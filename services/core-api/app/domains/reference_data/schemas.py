from datetime import date

from pydantic import BaseModel, ConfigDict


class ProvinceOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    code: int
    name_th: str
    name_en: str


class DistrictOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    code: int
    name_th: str
    name_en: str
    province_code: int


class SubdistrictOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    code: int
    name_th: str
    name_en: str
    postal_code: str
    district_code: int


class HolidayOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    date: date
    observed_date: date
    name_th: str
    name_en: str
    is_shifted: bool
    description: str | None
