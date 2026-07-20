import hashlib
import secrets
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from neurix_shared.models import ApiKey, AuthProvider, Plan, Subscription, SubscriptionStatus, User

_FREE_PLAN_NAME = "Free"
_FREE_PLAN_RATE_LIMIT = 60


async def get_user_by_email(session: AsyncSession, email: str) -> User | None:
    return await session.scalar(select(User).where(User.email == email))


async def create_user(session: AsyncSession, email: str, password_hash: str) -> User:
    user = User(email=email, auth_provider=AuthProvider.PASSWORD, password_hash=password_hash)
    session.add(user)
    await session.flush()
    return user


async def get_or_create_free_plan(session: AsyncSession) -> Plan:
    plan = await session.scalar(select(Plan).where(Plan.name == _FREE_PLAN_NAME))
    if plan is not None:
        return plan
    plan = Plan(name=_FREE_PLAN_NAME, rate_limit_per_min=_FREE_PLAN_RATE_LIMIT, price=0)
    session.add(plan)
    await session.flush()
    return plan


async def create_subscription(session: AsyncSession, user_id: uuid.UUID, plan_id: uuid.UUID) -> Subscription:
    subscription = Subscription(user_id=user_id, plan_id=plan_id)
    session.add(subscription)
    await session.flush()
    return subscription


async def get_active_subscription(session: AsyncSession, user_id: uuid.UUID) -> Subscription | None:
    # P0 assumes one active subscription per user — no plan-switching UI yet, so "first
    # active one" is unambiguous today. Revisit if/when multiple concurrent plans ship.
    return await session.scalar(
        select(Subscription).where(
            Subscription.user_id == user_id, Subscription.status == SubscriptionStatus.ACTIVE
        )
    )


async def list_subscriptions_with_plan(session: AsyncSession, user_id: uuid.UUID) -> list[dict]:
    result = await session.execute(
        select(Plan.name, Subscription.status)
        .join(Plan, Plan.id == Subscription.plan_id)
        .where(Subscription.user_id == user_id)
    )
    return [{"plan_name": name, "status": status.value} for name, status in result.all()]


async def list_api_keys_for_subscription(session: AsyncSession, subscription_id: uuid.UUID) -> list[ApiKey]:
    result = await session.execute(
        select(ApiKey).where(ApiKey.subscription_id == subscription_id).order_by(ApiKey.created_at.desc())
    )
    return list(result.scalars().all())


async def list_api_keys_for_user(session: AsyncSession, user_id: uuid.UUID) -> list[ApiKey]:
    result = await session.execute(
        select(ApiKey)
        .join(Subscription, Subscription.id == ApiKey.subscription_id)
        .where(Subscription.user_id == user_id)
        .order_by(ApiKey.created_at.desc())
    )
    return list(result.scalars().all())


def generate_raw_api_key() -> str:
    return f"nrx_{secrets.token_hex(20)}"  # same shape as scripts/seed.py's test key


def hash_api_key(raw_key: str) -> str:
    return hashlib.sha256(raw_key.encode()).hexdigest()


async def create_api_key(session: AsyncSession, subscription_id: uuid.UUID, raw_key: str) -> ApiKey:
    api_key = ApiKey(subscription_id=subscription_id, key_hash=hash_api_key(raw_key), key_prefix=raw_key[:12])
    session.add(api_key)
    await session.flush()
    return api_key


async def get_api_key_for_user(session: AsyncSession, user_id: uuid.UUID, api_key_id: uuid.UUID) -> ApiKey | None:
    return await session.scalar(
        select(ApiKey)
        .join(Subscription, Subscription.id == ApiKey.subscription_id)
        .where(ApiKey.id == api_key_id, Subscription.user_id == user_id)
    )
