from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "postgresql+asyncpg://neurix:neurix@localhost:5432/neurix"
    redis_url: str = "redis://localhost:6379/0"
    tmd_api_token: str = ""
    bot_api_token: str = ""

    # No insecure default — services/core-api/app/core/auth.py fails fast at import if
    # this is empty, rather than silently signing tokens with a guessable value.
    jwt_secret: str = ""
    apisix_admin_url: str = "http://apisix:9180"
    apisix_admin_key: str = ""

    # "log" (default) writes the verification link to the app's own logs instead of
    # sending real email — deliberate for now, not a placeholder left in by mistake: see
    # app/core/mailer.py. Swap to "resend"/"smtp" once a provider is actually chosen.
    mailer_backend: str = "log"
    portal_base_url: str = "http://localhost:3000"


settings = Settings()
