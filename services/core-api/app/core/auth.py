import uuid
from datetime import datetime, timedelta, timezone

from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_session
from neurix_shared.config import settings
from neurix_shared.models import User

if not settings.jwt_secret:
    raise RuntimeError(
        "JWT_SECRET is not set. Refusing to start with an empty/guessable signing key "
        "— set it in infra/.env (e.g. `openssl rand -hex 32`)."
    )

_ALGORITHM = "HS256"
_ACCESS_TOKEN_TTL = timedelta(days=7)
_password_hasher = PasswordHasher()  # Argon2id, slow/salted — see User.password_hash's comment for why
_bearer_scheme = HTTPBearer()


def hash_password(raw: str) -> str:
    return _password_hasher.hash(raw)


def verify_password(raw: str, hashed: str) -> bool:
    try:
        _password_hasher.verify(hashed, raw)
        return True
    except VerifyMismatchError:
        return False


def create_access_token(user_id: uuid.UUID) -> str:
    payload = {"sub": str(user_id), "exp": datetime.now(timezone.utc) + _ACCESS_TOKEN_TTL}
    return jwt.encode(payload, settings.jwt_secret, algorithm=_ALGORITHM)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(_bearer_scheme),
    session: AsyncSession = Depends(get_session),
) -> User:
    unauthorized = HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token")
    try:
        payload = jwt.decode(credentials.credentials, settings.jwt_secret, algorithms=[_ALGORITHM])
        user_id = uuid.UUID(payload["sub"])
    except (JWTError, KeyError, ValueError) as exc:
        raise unauthorized from exc

    user = await session.get(User, user_id)
    if user is None:
        raise unauthorized
    return user
