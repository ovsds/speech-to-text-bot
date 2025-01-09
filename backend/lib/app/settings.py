import warnings

import pydantic

import lib.utils.logging as logging_utils
import lib.utils.pydantic as pydantic_utils


class AppSettings(pydantic_utils.BaseSettingsModel):
    env: str = "production"
    debug: bool = False
    version: str = "unknown"

    @property
    def is_development(self) -> bool:
        return self.env == "development"

    @property
    def is_debug(self) -> bool:
        if not self.is_development and self.debug:
            warnings.warn("APP_DEBUG is True in non-development environment", UserWarning)

        return self.debug


class LoggingSettings(pydantic_utils.BaseSettingsModel):
    level: logging_utils.LogLevel = "INFO"
    format: str = "%(asctime)s | %(name)s | %(levelname)s | %(message)s"


class ServerSettings(pydantic_utils.BaseSettingsModel):
    host: str = "localhost"
    port: int = 8080
    public_host: str = NotImplemented


class TelegramSettings(pydantic_utils.BaseSettingsModel):
    token: str = NotImplemented
    bot_name: str = "SpeechToTextBot"
    bot_short_description: str = "Speech to text bot"
    bot_description: str = "Speech to text bot"
    admin_ids: list[int] = []
    allowed_user_ids: list[int] = []

    webhook_enabled: bool = True
    webhook_url: str = "/api/v1/telegram/webhook"
    webhook_secret_token: str = NotImplemented


class Settings(pydantic_utils.BaseSettings):
    app: AppSettings = pydantic.Field(default_factory=AppSettings)
    logs: LoggingSettings = pydantic.Field(default_factory=LoggingSettings)
    server: ServerSettings = pydantic.Field(default_factory=ServerSettings)
    telegram: TelegramSettings = pydantic.Field(default_factory=TelegramSettings)

    thread_pool_executor_max_workers: int = 10


__all__ = [
    "Settings",
]
