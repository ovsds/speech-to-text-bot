import contextlib
import dataclasses
import typing

import aiobotocore.session as aiobotocore_session

if typing.TYPE_CHECKING:
    import types_aiobotocore_s3

    AiobotocoreS3Client = types_aiobotocore_s3.S3Client
else:
    import aiobotocore.client as aiobotocore_client

    AiobotocoreS3Client = aiobotocore_client.AioBaseClient


@dataclasses.dataclass
class S3ClientContext:
    session: aiobotocore_session.AioSession
    endpoint_url: str
    access_key: str
    secret_key: str

    _exit_stack: contextlib.AsyncExitStack = dataclasses.field(init=False)

    async def __aenter__(self) -> AiobotocoreS3Client:
        self._exit_stack = contextlib.AsyncExitStack()
        client_creator_context = self.session.create_client(
            service_name="s3",
            endpoint_url=self.endpoint_url,
            aws_access_key_id=self.access_key,
            aws_secret_access_key=self.secret_key,
        )
        client = await self._exit_stack.enter_async_context(client_creator_context)
        return typing.cast(AiobotocoreS3Client, client)

    async def __aexit__(self, exc_type: typing.Any, exc: typing.Any, tb: typing.Any) -> None:
        await self._exit_stack.__aexit__(exc_type, exc, tb)


@dataclasses.dataclass
class S3Client:
    client_context: S3ClientContext

    class AlreadyExistsError(Exception): ...

    class NotFoundError(Exception): ...

    async def is_ready(self) -> bool:
        try:
            async with self.client_context as client:
                await client.list_buckets()
        except Exception:
            return False
        return True

    async def create(
        self,
        bucket_name: str,
        key: str,
        data: bytes,
    ) -> None:
        async with self.client_context as client:
            try:
                await client.put_object(
                    Bucket=bucket_name,
                    Key=key,
                    Body=data,
                    IfNoneMatch="*",
                )
            except client.exceptions.ClientError as exc:
                if exc.response["Error"]["Code"] == "PreconditionFailed":
                    raise self.AlreadyExistsError from exc

                raise

    async def read(
        self,
        bucket_name: str,
        key: str,
    ) -> bytes:
        async with self.client_context as client:
            try:
                response = await client.get_object(
                    Bucket=bucket_name,
                    Key=key,
                )
            except client.exceptions.NoSuchKey as exc:
                raise self.NotFoundError from exc
            return typing.cast(bytes, await response["Body"].read())

    async def delete(
        self,
        bucket_name: str,
        key: str,
    ) -> None:
        async with self.client_context as client:
            await client.delete_object(
                Bucket=bucket_name,
                Key=key,
            )


__all__ = [
    "S3Client",
    "S3ClientContext",
]
