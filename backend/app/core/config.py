from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file="backend/.env", extra="ignore")

    app_env: str = "development"
    frontend_origin: str = "http://localhost:3000"
    database_url: str = "sqlite:///./creatoros.db"

    supabase_url: str | None = None
    supabase_jwt_secret: str | None = None
    supabase_service_role_key: str | None = None

    openai_api_key: str | None = None
    openai_model: str = "gpt-5-mini"

    redis_url: str = "redis://localhost:6379/0"

    telegram_bot_token: str | None = None
    telegram_webhook_secret: str | None = None

    youtube_api_key: str | None = None
    youtube_oauth_client_id: str | None = None
    youtube_oauth_client_secret: str | None = None

    lemonsqueezy_api_key: str | None = None
    lemonsqueezy_store_id: str | None = None
    lemonsqueezy_webhook_secret: str | None = None
    lemonsqueezy_starter_variant_id: str | None = None
    lemonsqueezy_pro_variant_id: str | None = None
    lemonsqueezy_agency_variant_id: str | None = None


@lru_cache
def get_settings() -> Settings:
    return Settings()
