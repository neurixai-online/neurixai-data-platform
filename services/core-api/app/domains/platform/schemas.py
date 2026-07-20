import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class SignupIn(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=200)


class SignupOut(BaseModel):
    message: str


class LoginIn(BaseModel):
    email: EmailStr
    password: str
    totp_code: str | None = None


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"


class MfaSetupOut(BaseModel):
    secret: str
    otpauth_uri: str


class MfaCodeIn(BaseModel):
    code: str


class VerifyEmailIn(BaseModel):
    token: str


class ResendVerificationIn(BaseModel):
    email: EmailStr


class MessageOut(BaseModel):
    message: str


class SubscriptionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    plan_name: str
    status: str


class ApiKeyOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    key_prefix: str
    created_at: datetime
    revoked_at: datetime | None


class ApiKeyCreatedOut(ApiKeyOut):
    raw_key: str  # shown exactly once — caller must copy it now, we never show it again


class MeOut(BaseModel):
    id: uuid.UUID
    email: str
    totp_enabled: bool
    subscriptions: list[SubscriptionOut]
    api_keys: list[ApiKeyOut]
