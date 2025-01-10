import dataclasses
import logging
import typing

import lib.voice.clients as voice_clients
import lib.voice.models as voice_models
import lib.voice.services.protocols as protocols

logger = logging.getLogger(__name__)


@dataclasses.dataclass(frozen=True)
class Recognition(protocols.RecognitionProtocol):
    splitter_client: voice_clients.SplitterProtocol
    recognition_client: voice_clients.RecognitionProtocol

    async def recognize(
        self,
        audio: voice_models.Audio,
    ) -> typing.AsyncIterator[voice_models.RecognitionResult]:
        async for item in self.splitter_client.split(audio):
            recognized = await self.recognition_client.recognize(item)
            yield recognized


__all__ = [
    "Recognition",
]
