import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.apisix_client import consumer_name_for_api_key, create_consumer, delete_consumer
from app.core.auth import create_access_token, get_current_user, hash_password, verify_password
from app.core.db import get_session
from app.domains.platform import repository
from app.domains.platform.schemas import (
    ApiKeyCreatedOut,
    ApiKeyOut,
    LoginIn,
    MeOut,
    SignupIn,
    TokenOut,
)
from neurix_shared.models import User

router = APIRouter(prefix="/v1/platform", tags=["platform"])


@router.post("/auth/signup", response_model=TokenOut, status_code=status.HTTP_201_CREATED)
async def signup(body: SignupIn, session: AsyncSession = Depends(get_session)) -> TokenOut:
    if await repository.get_user_by_email(session, body.email) is not None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered")

    user = await repository.create_user(session, body.email, hash_password(body.password))
    free_plan = await repository.get_or_create_free_plan(session)
    await repository.create_subscription(session, user.id, free_plan.id)
    await session.commit()

    return TokenOut(access_token=create_access_token(user.id))


@router.post("/auth/login", response_model=TokenOut)
async def login(body: LoginIn, session: AsyncSession = Depends(get_session)) -> TokenOut:
    invalid = HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password")

    user = await repository.get_user_by_email(session, body.email)
    if user is None or user.password_hash is None or not verify_password(body.password, user.password_hash):
        raise invalid

    return TokenOut(access_token=create_access_token(user.id))


@router.get("/me", response_model=MeOut)
async def me(
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> MeOut:
    subscriptions = await repository.list_subscriptions_with_plan(session, user.id)
    api_keys = await repository.list_api_keys_for_user(session, user.id)
    return MeOut(id=user.id, email=user.email, subscriptions=subscriptions, api_keys=api_keys)


@router.post("/api-keys", response_model=ApiKeyCreatedOut, status_code=status.HTTP_201_CREATED)
async def create_api_key(
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> ApiKeyCreatedOut:
    subscription = await repository.get_active_subscription(session, user.id)
    if subscription is None:
        # Shouldn't happen — signup always creates one — but a clear 409 beats a 500 if it ever does.
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="No active subscription")

    raw_key = repository.generate_raw_api_key()
    api_key = await repository.create_api_key(session, subscription.id, raw_key)

    # Consumer must exist in APISIX before we commit-and-tell-the-user "here's your key" —
    # otherwise we could hand back a key that doesn't actually work through the gateway.
    await create_consumer(username=consumer_name_for_api_key(api_key.id), api_key=raw_key)
    await session.commit()

    return ApiKeyCreatedOut(
        id=api_key.id,
        key_prefix=api_key.key_prefix,
        created_at=api_key.created_at,
        revoked_at=api_key.revoked_at,
        raw_key=raw_key,
    )


@router.delete("/api-keys/{api_key_id}", response_model=ApiKeyOut)
async def revoke_api_key(
    api_key_id: uuid.UUID,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> ApiKeyOut:
    api_key = await repository.get_api_key_for_user(session, user.id, api_key_id)
    if api_key is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="API key not found")
    if api_key.revoked_at is None:
        api_key.revoked_at = datetime.now(timezone.utc)
        # Delete the gateway consumer BEFORE committing our own revoked_at, so a crash
        # between the two never leaves a key that's "revoked" in our DB but still live
        # at the gateway.
        await delete_consumer(username=consumer_name_for_api_key(api_key.id))
        await session.commit()
    return api_key
