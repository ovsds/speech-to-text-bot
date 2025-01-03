import typing

import lib.voice.models as voice_models


class SplitterClientProtocol(typing.Protocol):
    def split(self, audio: voice_models.Audio) -> typing.AsyncIterator[voice_models.Audio]: ...


__all__ = [
    "SplitterClientProtocol",
]
