from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "postgresql://ledgerlite:ledgerlite_dev@localhost:5432/ledgerlite"
    redis_url: str = "redis://localhost:6379/7"
    jwt_secret: str = "dev-secret-change-in-production"
    jwt_algorithm: str = "HS256"
    allowed_origins: list[str] = ["http://localhost:3000", "http://localhost:8080", "http://localhost:19006"]

    @property
    def async_database_url(self) -> str:
        return self.database_url.replace("postgresql://", "postgresql+asyncpg://", 1)

    model_config = {"env_prefix": "SYNC_"}


settings = Settings()
