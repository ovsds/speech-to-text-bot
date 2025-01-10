import dataclasses
import typing
import uuid

import temporalio.activity as temporalio_activity

import lib.app.client as app_client
import lib.voice.clients as voice_clients
import lib.voice.models as voice_models


@dataclasses.dataclass(frozen=True)
class Splitter:
    splitter_client: voice_clients.SplitterProtocol
    storage_client: voice_clients.StorageProtocol

    name: typing.ClassVar[str] = "splitter"

    @dataclasses.dataclass(frozen=True)
    class Params:
        audio_id: uuid.UUID

    @temporalio_activity.defn(name=name)
    async def run(self, params: Params) -> list[uuid.UUID]:
        audio = await self.storage_client.read(params.audio_id)

        result: list[uuid.UUID] = []
        async for item in self.splitter_client.split(audio):
            id = uuid.uuid4()
            await self.storage_client.create(id, item)
            result.append(id)

        return result


@dataclasses.dataclass(frozen=True)
class Recognition:
    recognition_client: voice_clients.RecognitionProtocol
    storage_client: voice_clients.StorageProtocol

    name: typing.ClassVar[str] = "recognition"

    @dataclasses.dataclass(frozen=True)
    class Params:
        audio_id: uuid.UUID

    @temporalio_activity.defn(name=name)
    async def run(self, params: Params) -> voice_models.RecognitionResult:
        audio = await self.storage_client.read(params.audio_id)
        return await self.recognition_client.recognize(audio)


@dataclasses.dataclass(frozen=True)
class Cleaner:
    storage_client: voice_clients.StorageProtocol

    name: typing.ClassVar[str] = "cleaner"

    @dataclasses.dataclass(frozen=True)
    class Params:
        audio_id: uuid.UUID

    @temporalio_activity.defn(name=name)
    async def run(self, params: Params) -> None:
        await self.storage_client.delete(params.audio_id)


@dataclasses.dataclass(frozen=True)
class Callback:
    main_app_client: app_client.AppClient

    name: typing.ClassVar[str] = "callback"

    @dataclasses.dataclass(frozen=True)
    class Params:
        audio_id: uuid.UUID

    @temporalio_activity.defn(name=name)
    async def run(self, params: Params) -> None:
        await self.main_app_client.media_callback(params.audio_id)


__all__ = [
    "Cleaner",
    "Recognition",
    "Splitter",
]
