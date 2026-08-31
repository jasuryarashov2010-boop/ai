from functools import lru_cache
import os
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    BOT_TOKEN: str
    ADMIN_IDS: str = ""
    DATABASE_URL: str
    REDIS_URL: str = ""
    PUBLIC_BASE_URL: str = ""
    WEBHOOK_PATH: str = "/telegram/webhook"

    OPENAI_API_KEY: str = ""
    OPENAI_MODEL: str = "gpt-4o-mini"
    OPENAI_VISION_MODEL: str = "gpt-4o-mini"
    OPENAI_TRANSCRIBE_MODEL: str = "gpt-4o-mini-transcribe"
    OPENAI_IMAGE_MODEL: str = "gpt-image-1"

    SUPPORT_USERNAME: str = ""
    BOT_NAME: str = "AI Yordamchi"
    LOG_LEVEL: str = "INFO"

    FREE_DAILY_AI: int = 20
    FREE_DAILY_VOICE: int = 3
    FREE_DAILY_FILE: int = 3
    FREE_DAILY_IMAGE: int = 1

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    @property
    def admin_ids(self) -> set[int]:
        return {int(x.strip()) for x in self.ADMIN_IDS.split(",") if x.strip().isdigit()}

    @property
    def external_url(self) -> str:
        return (self.PUBLIC_BASE_URL or os.getenv("RENDER_EXTERNAL_URL", "")).rstrip("/")

    @property
    def webhook_url(self) -> str:
        if not self.external_url:
            return ""
        return self.external_url + "/" + self.WEBHOOK_PATH.strip("/")

@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
