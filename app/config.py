# ---------------------------------------------------------------------------
# config.py
# Loads environment variables from .env using pydantic-settings.
# Import `settings` anywhere in the app — never read os.environ directly.
# ---------------------------------------------------------------------------

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    APP_NAME: str = "RenovaSim AI"
    APP_VERSION: str = "0.1.0"
    APP_DEBUG: bool = False
    APP_ENV: str = "development"
    DATABASE_URL: str = "sqlite:///./renovasim.db"

    # CORS — comma-separated list of allowed origins
    CORS_ORIGINS: str = "http://localhost:8080,http://localhost:3000"

    # API Key — set this in .env for production
    API_KEY: str = ""
    API_KEY_ENABLED: bool = False

    # Rate limiting
    RATE_LIMIT: str = "60/minute"
    RATE_LIMIT_AI: str = "10/minute"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
    )

    def get_cors_origins(self) -> list[str]:
        return [o.strip() for o in self.CORS_ORIGINS.split(",") if o.strip()]


settings = Settings()
TIMEOUT = 240.0