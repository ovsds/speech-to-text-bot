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
class S3Client:
    session: aiobotocore_session.AioSession
    endpoint_url: str
    access_key: str
    secret_key: str

    _exit_stack: contextlib.AsyncExitStack = dataclasses.field(default_factory=contextlib.AsyncExitStack, init=False)
    _client: AiobotocoreS3Client | None = dataclasses.field(default=None, init=False)

    @contextlib.asynccontextmanager
    async def client_context(self) -> typing.AsyncGenerator[AiobotocoreS3Client, None]:
        if self._client is None:
            client_creator_context = self.session.create_client(
                service_name="s3",
                endpoint_url=self.endpoint_url,
                aws_access_key_id=self.access_key,
                aws_secret_access_key=self.secret_key,
            )
            client = await self._exit_stack.enter_async_context(client_creator_context)
            self._client = typing.cast(AiobotocoreS3Client, client)

        yield self._client

    async def dispose(self) -> None:
        await self._exit_stack.aclose()

    class AlreadyExistsError(Exception): ...

    class NotFoundError(Exception): ...

    async def is_ready(self) -> bool:
        try:
            async with self.client_context() as client:
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
        async with self.client_context() as client:
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
        async with self.client_context() as client:
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
        async with self.client_context() as client:
            await client.delete_object(
                Bucket=bucket_name,
                Key=key,
            )


__all__ = [
    "S3Client",
]
