import dataclasses
import logging
import typing
import uuid

import aiohttp.web as aiohttp_web

import lib.utils.aiohttp as aiohttp_utils
import lib.utils.pydantic as pydantic_utils
import lib.voice.services.protocols as voice_service_protocols

logger = logging.getLogger(__name__)


class CallbackProcessor(typing.Protocol):
    async def __call__(self, audio_id: uuid.UUID) -> None: ...


@dataclasses.dataclass(frozen=True)
class MediaCallbackHandler:
    recognition_task_service: voice_service_protocols.RecognitionTaskProtocol
    callback_processor: CallbackProcessor

    method: typing.ClassVar[str] = "POST"
    path: typing.ClassVar[str] = "/api/v1/callback/media"

    class RequestSchema(pydantic_utils.BaseSchema):
        audio_id: uuid.UUID

    async def process(self, request: aiohttp_web.Request) -> aiohttp_web.Response:
        raw_data = await request.read()
        data = self.RequestSchema.from_json_bytes(raw_data)
        await self.callback_processor(
            audio_id=data.audio_id,
        )

        return aiohttp_utils.Response.with_data(
            status=200,
            data="OK",
        )


__all__ = [
    "MediaCallbackHandler",
]
