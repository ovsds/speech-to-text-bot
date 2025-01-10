import typing
import uuid

import lib.voice.models as voice_models


class StorageProtocol(typing.Protocol):
    class BaseError(Exception): ...

    class NotFoundError(BaseError): ...

    class AlreadyExistsError(BaseError): ...

    async def create(
        self,
        id: uuid.UUID,
        audio: voice_models.Audio,
    ) -> None:
        """
        :raises AlreadyExistsError: if audio with the same id already exists
        """
        ...

    async def read(
        self,
        id: uuid.UUID,
    ) -> voice_models.Audio:
        """
        :raises NotFoundError: if audio with the given id does not exist
        """
        ...

    async def delete(
        self,
        id: uuid.UUID,
    ) -> None: ...


__all__ = [
    "StorageProtocol",
]
