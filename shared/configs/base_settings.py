"""
Base settings shared across all microservices.

Each service creates its own Settings(BaseServiceSettings) subclass,
overriding env_prefix and adding service-specific fields.
"""

from pydantic_settings import BaseSettings


class BaseServiceSettings(BaseSettings):
    database_url: str = "postgresql://ledgerlite:ledgerlite_dev@localhost:5432/ledgerlite"
    redis_url: str = "redis://localhost:6379/0"
    jwt_secret: str = "dev-secret-change-in-production"
    jwt_algorithm: str = "HS256"

    @property
    def async_database_url(self) -> str:
        return self.database_url.replace("postgresql://", "postgresql+asyncpg://", 1)
