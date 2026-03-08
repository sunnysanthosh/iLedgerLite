from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "postgresql://ledgerlite:ledgerlite@localhost:5432/ledgerlite"
    redis_url: str = "redis://localhost:6379/0"
    jwt_secret: str = "dev-secret-change-in-production"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7
    allowed_origins: list[str] = ["http://localhost:3000", "http://localhost:8080", "http://localhost:19006"]

    @property
    def async_database_url(self) -> str:
        return self.database_url.replace("postgresql://", "postgresql+asyncpg://", 1)

    model_config = {"env_prefix": "AUTH_"}


settings = Settings()
