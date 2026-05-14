from functools import lru_cache

from pydantic import computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "Fleet Telemetry Monitor"
    database_url: str = (
        "postgresql+asyncpg://fleet:fleet@localhost:5432/fleet_telemetry"
    )

    @computed_field  # type: ignore[prop-decorator]
    @property
    def database_url_sync(self) -> str:
        """Sync SQLAlchemy URL for Alembic (psycopg2-binary)."""
        return self.database_url.replace(
            "postgresql+asyncpg://",
            "postgresql://",
        )


@lru_cache
def get_settings() -> Settings:
    return Settings()
