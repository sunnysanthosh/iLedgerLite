from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "postgresql://ledgerlite:ledgerlite_dev@localhost:5432/ledgerlite"
    redis_url: str = "redis://localhost:6379/6"
    jwt_secret: str = "dev-secret-change-in-production"
    jwt_algorithm: str = "HS256"
    allowed_origins: list[str] = ["http://localhost:3000", "http://localhost:8080", "http://localhost:19006"]

    # SMTP — all optional. Email is disabled when smtp_host is empty.
    smtp_host: str = ""
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_password: str = ""
    smtp_from: str = "noreply@iledger.app"

    @property
    def async_database_url(self) -> str:
        return self.database_url.replace("postgresql://", "postgresql+asyncpg://", 1)

    model_config = {"env_prefix": "NOTIFICATION_"}


settings = Settings()
