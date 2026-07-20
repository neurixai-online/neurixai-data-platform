import asyncio

import httpx
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from connectors.base import Connector
from neurix_shared.models import District, Province, Subdistrict

_BASE_URL = "https://raw.githubusercontent.com/thailand-geography-data/thailand-geography-json/main/src"
_PROVINCES_URL = f"{_BASE_URL}/provinces.json"
_DISTRICTS_URL = f"{_BASE_URL}/districts.json"
_SUBDISTRICTS_URL = f"{_BASE_URL}/subdistricts.json"


class ProvinceDistrictSubdistrictConnector(Connector):
    """Source: thailand-geography-data/thailand-geography-json (MIT licensed; verified
    reachable and schema-checked 2026-07-20 — 77 provinces / 928 districts / 7,436
    subdistricts, postal codes included at district+subdistrict level).

    Chosen as the first connector deliberately: it's static reference data with no
    external rate limit or auth to fight, so it proves the ingestion -> DB -> cache ->
    API -> gateway pipeline end to end before we touch flakier live sources (BOT FX,
    weather, PM2.5)."""

    source_name = "th_province_district_subdistrict"
    schedule_cron = "0 3 1 * *"  # monthly — this dataset is effectively static

    async def fetch(self, session: AsyncSession) -> dict:
        async with httpx.AsyncClient(timeout=30) as client:
            provinces_resp, districts_resp, subdistricts_resp = await asyncio.gather(
                client.get(_PROVINCES_URL),
                client.get(_DISTRICTS_URL),
                client.get(_SUBDISTRICTS_URL),
            )
        for resp in (provinces_resp, districts_resp, subdistricts_resp):
            resp.raise_for_status()
        return {
            "provinces": provinces_resp.json(),
            "districts": districts_resp.json(),
            "subdistricts": subdistricts_resp.json(),
        }

    async def transform(self, raw: dict) -> dict:
        return {
            "provinces": [
                {"code": p["provinceCode"], "name_th": p["provinceNameTh"], "name_en": p["provinceNameEn"]}
                for p in raw["provinces"]
            ],
            "districts": [
                {
                    "code": d["districtCode"],
                    "name_th": d["districtNameTh"],
                    "name_en": d["districtNameEn"],
                    "province_code": d["provinceCode"],
                }
                for d in raw["districts"]
            ],
            "subdistricts": [
                {
                    "code": s["subdistrictCode"],
                    "name_th": s["subdistrictNameTh"],
                    "name_en": s["subdistrictNameEn"],
                    "postal_code": str(s["postalCode"]),
                    "district_code": s["districtCode"],
                }
                for s in raw["subdistricts"]
            ],
        }

    async def load(self, session: AsyncSession, records: dict) -> int:
        # Order matters: provinces -> districts -> subdistricts, because each level's
        # upsert needs the parent's internal id, which only exists once the parent
        # row has been upserted and its id returned.
        province_id_by_code = await self._upsert_provinces(session, records["provinces"])
        district_id_by_code = await self._upsert_districts(session, records["districts"], province_id_by_code)
        await self._upsert_subdistricts(session, records["subdistricts"], district_id_by_code)
        return len(records["provinces"]) + len(records["districts"]) + len(records["subdistricts"])

    # Postgres/asyncpg cap a single prepared statement at 32,767 bind parameters. The
    # subdistricts table alone is ~7,436 rows x 5 columns (~37k params) — over the limit
    # in one shot — so every bulk upsert here is chunked. 1,000 rows/batch keeps every
    # table comfortably under the cap even as columns are added later.
    _BATCH_SIZE = 1000

    @staticmethod
    def _batched(items: list[dict], size: int) -> list[list[dict]]:
        return [items[i : i + size] for i in range(0, len(items), size)]

    async def _upsert_provinces(self, session: AsyncSession, items: list[dict]) -> dict[int, int]:
        id_by_code: dict[int, int] = {}
        for batch in self._batched(items, self._BATCH_SIZE):
            stmt = pg_insert(Province).values(batch)
            stmt = stmt.on_conflict_do_update(
                index_elements=[Province.code],
                set_={"name_th": stmt.excluded.name_th, "name_en": stmt.excluded.name_en},
            ).returning(Province.id, Province.code)
            result = await session.execute(stmt)
            id_by_code.update({code: id_ for id_, code in result.all()})
        return id_by_code

    async def _upsert_districts(
        self, session: AsyncSession, items: list[dict], province_id_by_code: dict[int, int]
    ) -> dict[int, int]:
        values = [
            {
                "code": d["code"],
                "name_th": d["name_th"],
                "name_en": d["name_en"],
                "province_id": province_id_by_code[d["province_code"]],
            }
            for d in items
        ]
        id_by_code: dict[int, int] = {}
        for batch in self._batched(values, self._BATCH_SIZE):
            stmt = pg_insert(District).values(batch)
            stmt = stmt.on_conflict_do_update(
                index_elements=[District.code],
                set_={
                    "name_th": stmt.excluded.name_th,
                    "name_en": stmt.excluded.name_en,
                    "province_id": stmt.excluded.province_id,
                },
            ).returning(District.id, District.code)
            result = await session.execute(stmt)
            id_by_code.update({code: id_ for id_, code in result.all()})
        return id_by_code

    async def _upsert_subdistricts(
        self, session: AsyncSession, items: list[dict], district_id_by_code: dict[int, int]
    ) -> None:
        values = [
            {
                "code": s["code"],
                "name_th": s["name_th"],
                "name_en": s["name_en"],
                "postal_code": s["postal_code"],
                "district_id": district_id_by_code[s["district_code"]],
            }
            for s in items
        ]
        for batch in self._batched(values, self._BATCH_SIZE):
            stmt = pg_insert(Subdistrict).values(batch)
            stmt = stmt.on_conflict_do_update(
                index_elements=[Subdistrict.code],
                set_={
                    "name_th": stmt.excluded.name_th,
                    "name_en": stmt.excluded.name_en,
                    "postal_code": stmt.excluded.postal_code,
                    "district_id": stmt.excluded.district_id,
                },
            )
            await session.execute(stmt)
