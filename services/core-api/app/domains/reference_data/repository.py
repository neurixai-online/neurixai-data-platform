from sqlalchemy import extract, select
from sqlalchemy.ext.asyncio import AsyncSession

from neurix_shared.models import District, Province, PublicHoliday, Subdistrict

# Explicit column-select + join, returned as plain dicts. Async SQLAlchemy does not support
# implicit lazy-loading of relationships outside an active await context (raises
# MissingGreenlet), so we never hand ORM instances with un-loaded relationships to the
# response layer — every field the API needs is fetched in the query itself.


async def list_provinces(session: AsyncSession) -> list[dict]:
    result = await session.execute(
        select(Province.code, Province.name_th, Province.name_en).order_by(Province.code)
    )
    return [dict(row) for row in result.mappings().all()]


async def list_districts(session: AsyncSession, province_code: int) -> list[dict]:
    result = await session.execute(
        select(
            District.code,
            District.name_th,
            District.name_en,
            Province.code.label("province_code"),
        )
        .join(Province, Province.id == District.province_id)
        .where(Province.code == province_code)
        .order_by(District.code)
    )
    return [dict(row) for row in result.mappings().all()]


async def list_subdistricts(session: AsyncSession, district_code: int) -> list[dict]:
    result = await session.execute(
        select(
            Subdistrict.code,
            Subdistrict.name_th,
            Subdistrict.name_en,
            Subdistrict.postal_code,
            District.code.label("district_code"),
        )
        .join(District, District.id == Subdistrict.district_id)
        .where(District.code == district_code)
        .order_by(Subdistrict.code)
    )
    return [dict(row) for row in result.mappings().all()]


async def list_holidays(session: AsyncSession, year: int | None) -> list[dict]:
    stmt = select(
        PublicHoliday.date,
        PublicHoliday.observed_date,
        PublicHoliday.name_th,
        PublicHoliday.name_en,
        PublicHoliday.is_shifted,
        PublicHoliday.description,
    ).order_by(PublicHoliday.date)
    if year is not None:
        stmt = stmt.where(extract("year", PublicHoliday.date) == year)

    result = await session.execute(stmt)
    # date/observed_date are Python `date` objects here — not JSON-serializable as-is,
    # and this dict is what gets cached (see CacheRepository.set_json), so convert to
    # ISO strings now. Pydantic's HolidayOut still parses them back into `date` fine.
    return [
        {**dict(row), "date": row["date"].isoformat(), "observed_date": row["observed_date"].isoformat()}
        for row in result.mappings().all()
    ]
