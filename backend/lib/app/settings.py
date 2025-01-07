import os
import typing
import warnings

import pydantic
import pydantic_settings

import lib.utils.logging as logging_utils


class AppSettings(pydantic.BaseModel):
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


class LoggingSettings(pydantic.BaseModel):
    level: logging_utils.LogLevel = "INFO"
    format: str = "%(asctime)s | %(name)s | %(levelname)s | %(message)s"


class ServerSettings(pydantic.BaseModel):
    host: str = "localhost"
    port: int = 8080
    public_host: str = NotImplemented


class TelegramSettings(pydantic.BaseModel):
    token: str = NotImplemented
    bot_name: str = "SpeechToTextBot"
    bot_short_description: str = "Speech to text bot"
    bot_description: str = "Speech to text bot"
    admin_ids: list[int] = []
    allowed_user_ids: list[int] = []

    webhook_enabled: bool = True
    webhook_url: str = "/api/v1/telegram/webhook"
    webhook_secret_token: str = NotImplemented


class Settings(pydantic_settings.BaseSettings):
    app: AppSettings = pydantic.Field(default_factory=AppSettings)
    logs: LoggingSettings = pydantic.Field(default_factory=LoggingSettings)
    server: ServerSettings = pydantic.Field(default_factory=ServerSettings)
    telegram: TelegramSettings = pydantic.Field(default_factory=TelegramSettings)

    thread_pool_executor_max_workers: int = 10

    model_config = pydantic_settings.SettingsConfigDict(
        env_nested_delimiter="__",
    )

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls: type[pydantic_settings.BaseSettings],
        init_settings: pydantic_settings.PydanticBaseSettingsSource,
        env_settings: pydantic_settings.PydanticBaseSettingsSource,
        dotenv_settings: pydantic_settings.PydanticBaseSettingsSource,
        file_secret_settings: pydantic_settings.PydanticBaseSettingsSource,
    ) -> tuple[pydantic_settings.PydanticBaseSettingsSource, ...]:
        return (
            env_settings,
            *cls.settings_yaml_sources(settings_cls),
        )

    @classmethod
    def settings_yaml_sources(
        cls,
        settings_cls: type[pydantic_settings.BaseSettings],
    ) -> typing.Sequence[pydantic_settings.YamlConfigSettingsSource]:
        setting_yaml_env = os.environ.get("SETTINGS_YAML", None)

        if setting_yaml_env is None:
            return []

        paths = setting_yaml_env.split(":")

        for path in paths:
            if not os.path.exists(path):
                raise FileNotFoundError(f"Settings file not found: {path}")

        return [
            pydantic_settings.YamlConfigSettingsSource(
                settings_cls,
                yaml_file=path,
            )
            for path in paths
        ]


__all__ = [
    "Settings",
]
