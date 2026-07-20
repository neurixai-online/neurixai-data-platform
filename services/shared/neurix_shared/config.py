from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "postgresql+asyncpg://neurix:neurix@localhost:5432/neurix"
    redis_url: str = "redis://localhost:6379/0"
    tmd_api_token: str = ""

    # No insecure default — services/core-api/app/core/auth.py fails fast at import if
    # this is empty, rather than silently signing tokens with a guessable value.
    jwt_secret: str = ""
    apisix_admin_url: str = "http://apisix:9180"
    apisix_admin_key: str = ""


settings = Settings()
