import asyncio
import concurrent.futures as concurrent_futures
import dataclasses
import logging
import typing

import aiobotocore.session as aiobotocore_session
import aiohttp
import temporalio.client as temporalio_client
import temporalio.worker as temporalio_worker

import lib.app.client as app_client
import lib.app.errors as app_errors
import lib.temporal.activities as temporal_activities
import lib.temporal.worker.settings as temporal_worker_settings
import lib.temporal.workflows as temporal_workflows
import lib.utils.aiobotocore as aiobotocore_utils
import lib.utils.lifecycle as lifecycle_utils
import lib.utils.logging as logging_utils
import lib.voice.clients as voice_clients

logger = logging.getLogger(__name__)


@dataclasses.dataclass(frozen=True)
class Application:
    lifecycle: lifecycle_utils.Lifecycle

    @classmethod
    async def from_settings(cls, settings: temporal_worker_settings.Settings) -> typing.Self:
        # Logging

        log_level = "DEBUG" if settings.app.is_debug else settings.logs.level
        logging_config = logging_utils.create_config(
            log_level=log_level,
            log_format=settings.logs.format,
            loggers={
                "asyncio": logging_utils.LoggerConfig(
                    propagate=False,
                    level=log_level,
                ),
            },
        )
        logging_utils.initialize(config=logging_config)
        logger.info("Logging has been initialized with config: %s", logging_config)

        logger.info("Initializing application")

        lifecycle_main_tasks: list[asyncio.Task[typing.Any]] = []
        lifecycle_startup_callbacks: list[lifecycle_utils.Callback] = []
        lifecycle_shutdown_callbacks: list[lifecycle_utils.Callback] = []

        logger.info("Initializing global dependencies")

        aiohttp_client = aiohttp.ClientSession()
        lifecycle_shutdown_callbacks.append(
            lifecycle_utils.Callback.from_dispose(name="aiohttp_client", awaitable=aiohttp_client.close())
        )
        temporal_client = await temporalio_client.Client.connect(
            target_host=settings.temporalio.endpoint_url,
            namespace=settings.temporalio.namespace,
        )
        loop = asyncio.get_running_loop()
        thread_pool_executor = concurrent_futures.ThreadPoolExecutor(max_workers=10)

        logger.info("Initializing clients")

        conversion_client = voice_clients.PydubConversion(
            loop=loop,
            thread_pool_executor=thread_pool_executor,
        )
        splitter_client = voice_clients.PydubOnSilenceSplitter(
            loop=loop,
            thread_pool_executor=thread_pool_executor,
            conversion_client=conversion_client,
        )
        recognition_client = voice_clients.SpeechRecognition(
            loop=loop,
            thread_pool_executor=thread_pool_executor,
            conversion_client=conversion_client,
        )
        if isinstance(settings.audio_storage, temporal_worker_settings.S3AudioStorageSettings):
            audio_storage_s3_client = aiobotocore_utils.S3Client(
                session=aiobotocore_session.AioSession(),
                endpoint_url=settings.audio_storage.s3.endpoint_url,
                access_key=settings.audio_storage.s3.access_key,
                secret_key=settings.audio_storage.s3.secret_key,
            )
            lifecycle_shutdown_callbacks.append(
                lifecycle_utils.Callback.from_dispose(
                    name="audio_storage_s3_client",
                    awaitable=audio_storage_s3_client.dispose(),
                )
            )
            audio_storage_client = voice_clients.S3Storage(
                s3_client=audio_storage_s3_client,
                bucket_name=settings.audio_storage.s3.bucket_name,
            )
        else:
            raise NotImplementedError(f"Unsupported audio storage type: {settings.audio_storage.type_name}")
        main_app_client = app_client.AppClient(
            aiohttp_client=aiohttp_client,
            base_url=settings.main_app_url,
        )

        logger.info("Initializing temporal activities")

        recognition_activity = temporal_activities.Recognition(
            recognition_client=recognition_client,
            storage_client=audio_storage_client,
        )
        splitter_activity = temporal_activities.Splitter(
            splitter_client=splitter_client,
            storage_client=audio_storage_client,
        )
        cleaner_activity = temporal_activities.Cleaner(
            storage_client=audio_storage_client,
        )
        callback_activity = temporal_activities.Callback(
            main_app_client=main_app_client,
        )

        logger.info("Initializing temporal worker")

        temporal_worker = temporalio_worker.Worker(
            client=temporal_client,
            task_queue=settings.temporalio.task_queue,
            workflows=[temporal_workflows.Recognition],
            activities=[
                recognition_activity.run,
                splitter_activity.run,
                cleaner_activity.run,
                callback_activity.run,
            ],
        )
        lifecycle_main_tasks.append(loop.create_task(temporal_worker.run()))
        lifecycle_shutdown_callbacks.append(
            lifecycle_utils.Callback.from_dispose(name="temporal_worker", awaitable=temporal_worker.shutdown())
        )

        logger.info("Initializing lifecycle manager")

        lifecycle = lifecycle_utils.Lifecycle(
            logger=logger,
            main_tasks=lifecycle_main_tasks,
            startup_callbacks=lifecycle_startup_callbacks,
            shutdown_callbacks=list(reversed(lifecycle_shutdown_callbacks)),
        )

        logger.info("Creating application")
        application = cls(
            lifecycle=lifecycle,
        )

        logger.info("Initializing application finished")

        return application

    async def start(self) -> None:
        try:
            await self.lifecycle.on_startup()
        except lifecycle_utils.Lifecycle.StartupError as start_error:
            logger.error("Application has failed to start")
            raise app_errors.ServerStartError("Application has failed to start, see logs above") from start_error

        logger.info("Application is starting")
        try:
            await self.lifecycle.run()
        except asyncio.CancelledError:
            logger.info("Application has been interrupted")
        except BaseException as unexpected_error:
            logger.exception("Application runtime error")
            raise app_errors.ServerRuntimeError("Application runtime error") from unexpected_error

    async def dispose(self) -> None:
        logger.info("Application is shutting down...")

        try:
            await self.lifecycle.on_shutdown()
        except lifecycle_utils.Lifecycle.ShutdownError as dispose_error:
            logger.error("Application has shut down with errors")
            raise app_errors.DisposeError("Application has shut down with errors, see logs above") from dispose_error

        logger.info("Application has successfully shut down")


__all__ = [
    "Application",
]
