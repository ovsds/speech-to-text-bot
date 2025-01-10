import dataclasses
import uuid

import lib.utils.aiobotocore as aiobotocore_utils
import lib.voice.clients.storage.protocol as protocol
import lib.voice.models as voice_models
import lib.voice.schemas as voice_schemas


@dataclasses.dataclass
class S3Storage(protocol.StorageProtocol):
    s3_client: aiobotocore_utils.S3Client
    bucket_name: str
    key_prefix: str = "audio"

    def _prepare_key(self, id: uuid.UUID) -> str:
        return f"{self.key_prefix}/{id}"

    async def create(
        self,
        id: uuid.UUID,
        audio: voice_models.Audio,
    ) -> None:
        data = voice_schemas.Audio.from_dataclass(audio).to_bytes()

        try:
            await self.s3_client.create(
                bucket_name=self.bucket_name,
                key=self._prepare_key(id),
                data=data,
            )
        except self.s3_client.AlreadyExistsError as exc:
            raise self.AlreadyExistsError from exc

    async def read(
        self,
        id: uuid.UUID,
    ) -> voice_models.Audio:
        try:
            data = await self.s3_client.read(
                bucket_name=self.bucket_name,
                key=self._prepare_key(id),
            )
        except self.s3_client.NotFoundError as exc:
            raise self.NotFoundError from exc

        return voice_schemas.Audio.from_bytes(data).to_dataclass()

    async def delete(
        self,
        id: uuid.UUID,
    ) -> None:
        await self.s3_client.delete(
            bucket_name=self.bucket_name,
            key=self._prepare_key(id),
        )


__all__ = [
    "S3Storage",
]
