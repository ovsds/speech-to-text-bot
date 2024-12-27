import typing

import lib.voice.models as voice_models


class ConversionClientProtocol(typing.Protocol):
    async def convert(self, audio: voice_models.Audio, format: voice_models.AudioFormat) -> voice_models.Audio: ...


__all__ = [
    "ConversionClientProtocol",
]
