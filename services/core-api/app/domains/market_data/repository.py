from datetime import date

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from neurix_shared.models import ExchangeRate


async def list_exchange_rates(
    session: AsyncSession,
    currency_code: str | None,
    start_date: date | None,
    end_date: date | None,
) -> list[dict]:
    stmt = select(
        ExchangeRate.currency_code,
        ExchangeRate.currency_name_th,
        ExchangeRate.currency_name_en,
        ExchangeRate.rate_date,
        ExchangeRate.buying_sight,
        ExchangeRate.buying_transfer,
        ExchangeRate.selling,
        ExchangeRate.mid_rate,
    ).order_by(ExchangeRate.rate_date.desc(), ExchangeRate.currency_code)

    if currency_code is not None:
        stmt = stmt.where(ExchangeRate.currency_code == currency_code.upper())
    if start_date is not None:
        stmt = stmt.where(ExchangeRate.rate_date >= start_date)
    if end_date is not None:
        stmt = stmt.where(ExchangeRate.rate_date <= end_date)

    result = await session.execute(stmt)
    # rate_date is a Python date — not JSON-serializable as-is, and this dict is what
    # gets cached (see CacheRepository.set_json), so convert to an ISO string now.
    return [{**dict(row), "rate_date": row["rate_date"].isoformat()} for row in result.mappings().all()]
