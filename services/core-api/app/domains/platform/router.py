import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.apisix_client import consumer_name_for_api_key, create_consumer, delete_consumer
from app.core.auth import create_access_token, get_current_user, hash_password, verify_password
from app.core.cache import get_redis
from app.core.db import get_session
from app.core.mailer import mailer
from app.core.mfa import (
    assert_not_locked_out,
    clear_mfa_failures,
    generate_totp_secret,
    record_mfa_failure,
    totp_provisioning_uri,
    verify_totp_code,
)
from app.domains.platform import repository
from app.domains.platform.schemas import (
    ApiKeyCreatedOut,
    ApiKeyOut,
    LoginIn,
    MeOut,
    MessageOut,
    MfaCodeIn,
    MfaSetupOut,
    ResendVerificationIn,
    SignupIn,
    SignupOut,
    TokenOut,
    VerifyEmailIn,
)
from neurix_shared.config import settings
from neurix_shared.models import User
from redis.asyncio import Redis

router = APIRouter(prefix="/v1/platform", tags=["platform"])


def _verification_link(token: str) -> str:
    return f"{settings.portal_base_url}/verify-email?token={token}"


@router.post("/auth/signup", response_model=SignupOut, status_code=status.HTTP_201_CREATED)
async def signup(body: SignupIn, session: AsyncSession = Depends(get_session)) -> SignupOut:
    if await repository.get_user_by_email(session, body.email) is not None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered")

    user, token = await repository.create_user(session, body.email, hash_password(body.password))
    free_plan = await repository.get_or_create_free_plan(session)
    await repository.create_subscription(session, user.id, free_plan.id)
    await mailer.send_verification_email(user.email, _verification_link(token))
    await session.commit()

    return SignupOut(message="Signup successful. Please check your email to verify your account.")


@router.post("/auth/login", response_model=TokenOut)
async def login(
    body: LoginIn,
    session: AsyncSession = Depends(get_session),
    redis: Redis = Depends(get_redis),
) -> TokenOut:
    invalid = HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password")

    user = await repository.get_user_by_email(session, body.email)
    if user is None or user.password_hash is None or not verify_password(body.password, user.password_hash):
        raise invalid

    if user.email_verified_at is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="email_not_verified")

    if user.totp_enabled:
        if not body.totp_code:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="mfa_required")

        await assert_not_locked_out(redis, user.id)
        assert user.totp_secret is not None  # guaranteed by enable_totp() only running after a set secret
        if not verify_totp_code(user.totp_secret, body.totp_code):
            await record_mfa_failure(redis, user.id)
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="invalid_mfa_code")
        await clear_mfa_failures(redis, user.id)

    return TokenOut(access_token=create_access_token(user.id))


@router.post("/auth/verify-email", response_model=MessageOut)
async def verify_email(body: VerifyEmailIn, session: AsyncSession = Depends(get_session)) -> MessageOut:
    user = await repository.get_user_by_verification_token(session, body.token)
    if user is None or user.email_verification_token_expires_at is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid or expired token")
    if user.email_verification_token_expires_at < datetime.now(timezone.utc):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid or expired token")

    repository.mark_email_verified(user)
    await session.commit()

    return MessageOut(message="Email verified. You can now log in.")


@router.post("/auth/resend-verification", response_model=MessageOut)
async def resend_verification(
    body: ResendVerificationIn, session: AsyncSession = Depends(get_session)
) -> MessageOut:
    user = await repository.get_user_by_email(session, body.email)
    # Same response whether or not the account exists — don't let this endpoint be used
    # to enumerate registered emails.
    if user is not None and user.email_verified_at is None:
        token = await repository.set_new_verification_token(session, user)
        await mailer.send_verification_email(user.email, _verification_link(token))
        await session.commit()

    return MessageOut(message="If that email is registered and unverified, a new link has been sent.")


@router.get("/me", response_model=MeOut)
async def me(
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> MeOut:
    subscriptions = await repository.list_subscriptions_with_plan(session, user.id)
    api_keys = await repository.list_api_keys_for_user(session, user.id)
    return MeOut(
        id=user.id,
        email=user.email,
        totp_enabled=user.totp_enabled,
        subscriptions=subscriptions,
        api_keys=api_keys,
    )


@router.post("/mfa/setup", response_model=MfaSetupOut)
async def mfa_setup(
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> MfaSetupOut:
    if user.totp_enabled:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="MFA already enabled")

    secret = generate_totp_secret()
    repository.set_pending_totp_secret(user, secret)
    await session.commit()

    return MfaSetupOut(secret=secret, otpauth_uri=totp_provisioning_uri(secret, user.email))


@router.post("/mfa/verify", response_model=MessageOut)
async def mfa_verify(
    body: MfaCodeIn,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
    redis: Redis = Depends(get_redis),
) -> MessageOut:
    if user.totp_enabled:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="MFA already enabled")
    if user.totp_secret is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Call /mfa/setup first")

    await assert_not_locked_out(redis, user.id)
    if not verify_totp_code(user.totp_secret, body.code):
        await record_mfa_failure(redis, user.id)
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="invalid_mfa_code")
    await clear_mfa_failures(redis, user.id)

    repository.enable_totp(user)
    await session.commit()

    return MessageOut(message="MFA enabled.")


@router.post("/mfa/disable", response_model=MessageOut)
async def mfa_disable(
    body: MfaCodeIn,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
    redis: Redis = Depends(get_redis),
) -> MessageOut:
    if not user.totp_enabled or user.totp_secret is None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="MFA is not enabled")

    await assert_not_locked_out(redis, user.id)
    if not verify_totp_code(user.totp_secret, body.code):
        await record_mfa_failure(redis, user.id)
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="invalid_mfa_code")
    await clear_mfa_failures(redis, user.id)

    repository.disable_totp(user)
    await session.commit()

    return MessageOut(message="MFA disabled.")


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
