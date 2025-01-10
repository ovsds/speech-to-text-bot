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


class TemporalioSettings(pydantic_utils.BaseSettingsModel):
    host: str = NotImplemented
    port: int = NotImplemented
    namespace: str = NotImplemented
    task_queue: str = NotImplemented

    @property
    def endpoint_url(self) -> str:
        return f"{self.host}:{self.port}"


class S3Settings(pydantic_utils.BaseSettingsModel):
    host: str = NotImplemented
    port: int = NotImplemented
    bucket_name: str = NotImplemented
    access_key: str = NotImplemented
    secret_key: str = NotImplemented

    @property
    def endpoint_url(self) -> str:
        return f"http://{self.host}:{self.port}"


class BaseAudioStorageSettings(pydantic_utils.TypedBaseSettingsModel): ...


class S3AudioStorageSettings(BaseAudioStorageSettings):
    type_name: str = "s3"
    s3: S3Settings = pydantic.Field(default_factory=S3Settings)


BaseAudioStorageSettings.register("s3", S3AudioStorageSettings)


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


class BaseMediaHandlerSettings(pydantic_utils.TypedBaseSettingsModel): ...


class SynchronousMediaHandlerSettings(BaseMediaHandlerSettings):
    type_name: str = "synchronous"


class TemporalioMediaHandlerSettings(BaseMediaHandlerSettings):
    type_name: str = "temporalio"

    temporalio: TemporalioSettings = pydantic.Field(default_factory=TemporalioSettings)
    audio_storage: pydantic_utils.TypedAnnotation[BaseAudioStorageSettings] = NotImplemented

    split_timeout_seconds: int = 10 * 60  # 10 minutes
    recognition_timeout_seconds: int = 10 * 60  # 10 minutes
    clean_up_timeout_seconds: int = 60  # 1 minute


BaseMediaHandlerSettings.register("synchronous", SynchronousMediaHandlerSettings)
BaseMediaHandlerSettings.register("temporalio", TemporalioMediaHandlerSettings)


class Settings(pydantic_utils.BaseSettings):
    app: AppSettings = pydantic.Field(default_factory=AppSettings)
    logs: LoggingSettings = pydantic.Field(default_factory=LoggingSettings)
    server: ServerSettings = pydantic.Field(default_factory=ServerSettings)
    telegram: TelegramSettings = pydantic.Field(default_factory=TelegramSettings)
    media_handler: pydantic_utils.TypedAnnotation[BaseMediaHandlerSettings] = pydantic.Field(
        default_factory=SynchronousMediaHandlerSettings,
    )

    thread_pool_executor_max_workers: int = 10


__all__ = [
    "AppSettings",
    "BaseAudioStorageSettings",
    "LoggingSettings",
    "S3AudioStorageSettings",
    "S3Settings",
    "Settings",
    "TemporalioSettings",
]
