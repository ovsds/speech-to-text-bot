import dataclasses
import logging
import typing

import lib.voice.clients as voice_clients
import lib.voice.models as voice_models

logger = logging.getLogger(__name__)


def seconds_to_text(seconds: float) -> str:
    minutes = int(seconds // 60)
    seconds = int(seconds % 60)

    return f"{minutes:02d}:{seconds:02d}"


class RecognitionServiceProtocol(typing.Protocol):
    def recognize(
        self,
        audio: voice_models.Audio,
    ) -> typing.AsyncIterator[voice_models.RecognitionResult]: ...


@dataclasses.dataclass(frozen=True)
class RecognitionService:
    splitter_client: voice_clients.SplitterClientProtocol
    recognition_client: voice_clients.RecognitionClientProtocol

    async def recognize(
        self,
        audio: voice_models.Audio,
    ) -> typing.AsyncIterator[voice_models.RecognitionResult]:
        async for item in self.splitter_client.split(audio):
            recognized = await self.recognition_client.recognize(item)
            yield recognized


__all__ = [
    "RecognitionService",
    "RecognitionServiceProtocol",
]
