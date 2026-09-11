from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="POKER_", env_file=".env", extra="ignore")

    database_url: str = "postgresql+asyncpg://poker:poker@postgres:5432/poker"
    redis_url: str = "redis://redis:6379/0"
    starting_stack: int = 1_000
    small_blind: int = 5
    big_blind: int = 10
    reconnect_ttl_seconds: int = 900
    allowed_origins: str = "http://localhost:5173"

