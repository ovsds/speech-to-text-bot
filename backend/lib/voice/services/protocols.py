import typing
import uuid

import lib.voice.models as voice_models


class RecognitionTaskProtocol(typing.Protocol):
    async def add_task(self, audio: voice_models.Audio, task_metadata: str) -> None: ...

    async def get_result(self, audio_id: uuid.UUID) -> voice_models.RecognitionTaskResult: ...


class RecognitionProtocol(typing.Protocol):
    def recognize(
        self,
        audio: voice_models.Audio,
    ) -> typing.AsyncIterator[voice_models.RecognitionResult]: ...


__all__ = [
    "RecognitionProtocol",
    "RecognitionTaskProtocol",
]
