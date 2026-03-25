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

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
    )


# Single shared instance — import this everywhere
settings = Settings()