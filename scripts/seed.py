"""Seed the Milestone-0 test fixtures: one connector, one product, one plan, one user,
one subscription, one API key. Prints the raw API key once — same pattern the real
Developer Portal will use (only the hash is ever persisted).

Run from services/shared with neurix-shared installed, e.g.:
    cd services/shared && uv run python ../../scripts/seed.py
"""

import asyncio
import hashlib
import secrets

from sqlalchemy import select

from neurix_shared.db import async_session_factory
from neurix_shared.models import ApiKey, ApiProduct, AuthProvider, Connector, Plan, PlanProduct, Subscription, User

CONNECTOR_SOURCE_NAME = "th_province_district_subdistrict"  # must match connectors/province_district_subdistrict.py
PRODUCT_SLUG = "th-provinces-districts-subdistricts"
PLAN_NAME = "milestone0-test"
TEST_USER_EMAIL = "milestone0-test@neurixai.local"


async def get_or_create_connector(session) -> Connector:
    existing = await session.scalar(select(Connector).where(Connector.source_name == CONNECTOR_SOURCE_NAME))
    if existing:
        return existing
    connector = Connector(
        source_name=CONNECTOR_SOURCE_NAME,
        adapter_type="http_json",
        schedule_cron="0 3 1 * *",
        config={},
    )
    session.add(connector)
    await session.flush()
    return connector


async def get_or_create_product(session, connector: Connector) -> ApiProduct:
    existing = await session.scalar(select(ApiProduct).where(ApiProduct.slug == PRODUCT_SLUG))
    if existing:
        return existing
    product = ApiProduct(
        domain="reference_data",
        slug=PRODUCT_SLUG,
        endpoint_prefix="/v1/reference",
        connector_id=connector.id,
        cache_ttl_seconds=6 * 60 * 60,  # must match _CACHE_TTL_SECONDS in app/domains/reference_data/router.py
    )
    session.add(product)
    await session.flush()
    return product


async def get_or_create_plan(session) -> Plan:
    existing = await session.scalar(select(Plan).where(Plan.name == PLAN_NAME))
    if existing:
        return existing
    plan = Plan(name=PLAN_NAME, rate_limit_per_min=120, price=0)  # must match limit-count in apisix_setup.sh
    session.add(plan)
    await session.flush()
    return plan


async def ensure_plan_product(session, plan: Plan, product: ApiProduct) -> None:
    existing = await session.scalar(
        select(PlanProduct).where(PlanProduct.plan_id == plan.id, PlanProduct.product_id == product.id)
    )
    if not existing:
        session.add(PlanProduct(plan_id=plan.id, product_id=product.id))


async def get_or_create_user(session) -> User:
    existing = await session.scalar(select(User).where(User.email == TEST_USER_EMAIL))
    if existing:
        return existing
    user = User(email=TEST_USER_EMAIL, auth_provider=AuthProvider.PASSWORD, password_hash=None)
    session.add(user)
    await session.flush()
    return user


async def get_or_create_subscription(session, user: User, plan: Plan) -> Subscription:
    existing = await session.scalar(
        select(Subscription).where(Subscription.user_id == user.id, Subscription.plan_id == plan.id)
    )
    if existing:
        return existing
    subscription = Subscription(user_id=user.id, plan_id=plan.id)
    session.add(subscription)
    await session.flush()
    return subscription


async def create_api_key(session, subscription: Subscription) -> str:
    raw_key = f"nrx_{secrets.token_hex(20)}"
    key_hash = hashlib.sha256(raw_key.encode()).hexdigest()
    session.add(
        ApiKey(
            subscription_id=subscription.id,
            key_hash=key_hash,
            key_prefix=raw_key[:12],
        )
    )
    return raw_key


async def main() -> None:
    async with async_session_factory() as session:
        connector = await get_or_create_connector(session)
        product = await get_or_create_product(session, connector)
        plan = await get_or_create_plan(session)
        await ensure_plan_product(session, plan, product)
        user = await get_or_create_user(session)
        subscription = await get_or_create_subscription(session, user, plan)
        raw_key = await create_api_key(session, subscription)
        await session.commit()

    print("Seed complete.")
    print(f"Raw API key (shown once — pass to scripts/apisix_setup.sh): {raw_key}")


if __name__ == "__main__":
    asyncio.run(main())
