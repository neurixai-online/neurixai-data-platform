import uuid

import pyotp
from fastapi import HTTPException, status
from redis.asyncio import Redis

_ISSUER = "NeurixAI Data Platform"
_MAX_ATTEMPTS = 5
_LOCKOUT_WINDOW_SECONDS = 300


def generate_totp_secret() -> str:
    return pyotp.random_base32()


def totp_provisioning_uri(secret: str, email: str) -> str:
    return pyotp.totp.TOTP(secret).provisioning_uri(name=email, issuer_name=_ISSUER)


def verify_totp_code(secret: str, code: str) -> bool:
    # valid_window=1 tolerates one 30s step of clock drift either side, matching how
    # every mainstream authenticator app behaves.
    return pyotp.totp.TOTP(secret).verify(code, valid_window=1)


def _lockout_key(user_id: uuid.UUID) -> str:
    return f"mfa_fail:{user_id}"


async def assert_not_locked_out(redis: Redis, user_id: uuid.UUID) -> None:
    count = await redis.get(_lockout_key(user_id))
    if count is not None and int(count) >= _MAX_ATTEMPTS:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many incorrect codes. Try again in a few minutes.",
        )


async def record_mfa_failure(redis: Redis, user_id: uuid.UUID) -> None:
    key = _lockout_key(user_id)
    count = await redis.incr(key)
    if count == 1:
        await redis.expire(key, _LOCKOUT_WINDOW_SECONDS)


async def clear_mfa_failures(redis: Redis, user_id: uuid.UUID) -> None:
    await redis.delete(_lockout_key(user_id))
