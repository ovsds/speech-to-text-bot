import typing

import lib.voice.models as voice_models


class RecognitionProtocol(typing.Protocol):
    async def recognize(self, audio: voice_models.Audio) -> voice_models.RecognitionResult: ...


__all__ = [
    "RecognitionProtocol",
]
