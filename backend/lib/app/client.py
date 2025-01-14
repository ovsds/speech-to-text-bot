import dataclasses
import uuid

import aiohttp

import lib.aiohttp.handlers as aiohttp_handlers


@dataclasses.dataclass(frozen=True)
class AppClient:
    aiohttp_client: aiohttp.ClientSession
    base_url: str

    async def media_callback(self, audio_id: uuid.UUID) -> None:
        request = aiohttp_handlers.MediaCallbackHandler.RequestSchema(audio_id=audio_id)
        data = request.to_json_bytes()

        async with self.aiohttp_client.request(
            method=aiohttp_handlers.MediaCallbackHandler.method,
            url=f"{self.base_url}{aiohttp_handlers.MediaCallbackHandler.path}",
            data=data,
        ) as response:
            response.raise_for_status()


__all__ = [
    "AppClient",
]
