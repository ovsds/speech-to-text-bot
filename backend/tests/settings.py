import pydantic

import lib.app.settings as app_settings
import lib.utils.pydantic as pydantic_utils


class Settings(pydantic_utils.BaseSettings):
    SETTINGS_PATH = "SETTINGS_TEST_PATH"

    s3: app_settings.S3Settings = pydantic.Field(default_factory=app_settings.S3Settings)


__all__ = [
    "Settings",
]
