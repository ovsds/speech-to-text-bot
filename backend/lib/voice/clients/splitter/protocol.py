import typing

import lib.voice.models as voice_models


class SplitterClientProtocol(typing.Protocol):
    async def split(self, audio: voice_models.Audio) -> list[voice_models.Audio]: ...


__all__ = [
    "SplitterClientProtocol",
]
