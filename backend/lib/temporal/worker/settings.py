import pydantic

import lib.utils.pydantic as pydantic_utils
from lib.app.settings import (
    AppSettings,
    BaseAudioStorageSettings,
    LoggingSettings,
    S3AudioStorageSettings,
    TemporalioSettings,
)


class Settings(pydantic_utils.BaseSettings):
    SETTINGS_PATH = "SETTINGS_WORKER_PATH"

    app: AppSettings = pydantic.Field(default_factory=AppSettings)
    logs: LoggingSettings = pydantic.Field(default_factory=LoggingSettings)

    temporalio: TemporalioSettings = pydantic.Field(default_factory=TemporalioSettings)
    audio_storage: pydantic_utils.TypedAnnotation[BaseAudioStorageSettings] = NotImplemented

    main_app_url: str = NotImplemented
    thread_pool_executor_max_workers: int = 10


__all__ = [
    "AppSettings",
    "LoggingSettings",
    "S3AudioStorageSettings",
    "Settings",
    "TemporalioSettings",
]
