import pydantic

import lib.utils.pydantic as pydantic_utils
import lib.voice.models as voice_models


class Audio(pydantic_utils.BaseDataclassSchema[voice_models.Audio]):
    class Meta(pydantic_utils.BaseDataclassSchema.Meta):
        DATACLASS = voice_models.Audio

    data: bytes = pydantic.Field()
    duration_seconds: float
    format: voice_models.AudioFormat


__all__ = [
    "Audio",
]
