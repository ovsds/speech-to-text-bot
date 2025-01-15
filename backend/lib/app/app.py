import asyncio
import concurrent.futures as concurrent_futures
import dataclasses
import logging
import typing

import aiobotocore.session as aiobotocore_session
import aiogram
import aiogram.webhook.aiohttp_server as aiogram_aiohttp_webhook
import aiohttp
import aiohttp.typedefs as aiohttp_typedefs
import aiohttp.web as aiohttp_web
import temporalio.client as temporalio_client

import lib.aiogram.handlers as aiogram_handlers
import lib.aiohttp.handlers as aiohttp_handlers
import lib.app.errors as app_errors
import lib.app.settings as app_settings
import lib.utils.aiobotocore as aiobotocore_utils
import lib.utils.aiogram as aiogram_utils
import lib.utils.aiohttp as aiohttp_utils
import lib.utils.lifecycle as lifecycle_utils
import lib.utils.logging as logging_utils
import lib.voice.clients as voice_clients
import lib.voice.services as voice_services

logger = logging.getLogger(__name__)


@dataclasses.dataclass(frozen=True)
class Application:
    lifecycle: lifecycle_utils.Lifecycle

    @classmethod
    async def from_settings(cls, settings: app_settings.Settings) -> typing.Self:
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
                "TeleBot": logging_utils.LoggerConfig(
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

        logger.info("Initializing aiohttp")

        aiohttp_url_dispatcher = aiohttp_web.UrlDispatcher()
        aiohttp_middlewares: list[aiohttp_typedefs.Middleware] = []
        aiohttp_subsystem_readiness_callbacks: list[aiohttp_utils.SubsystemReadinessCallback] = []

        logger.info("Initializing global dependencies")

        loop = asyncio.get_event_loop()
        thread_pool_executor = concurrent_futures.ThreadPoolExecutor(
            max_workers=settings.thread_pool_executor_max_workers
        )

        aiohttp_client = aiohttp.ClientSession()
        lifecycle_shutdown_callbacks.append(
            lifecycle_utils.Callback.from_dispose(
                name="aiohttp_client",
                awaitable=aiohttp_client.close(),
            )
        )

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

        logger.info("Initializing repositories")

        logger.info("Initializing services")

        recognition_service = voice_services.Recognition(
            splitter_client=splitter_client,
            recognition_client=recognition_client,
        )

        logger.info("Initializing aiogram")

        aiogram_bot = aiogram.Bot(token=settings.telegram.token)
        aiogram_dispatcher = aiogram.Dispatcher()

        logger.info("Initializing aiogram common filters")

        aiogram_allowed_users_filter = aiogram_utils.SenderMessageFilter(
            user_ids=settings.telegram.allowed_user_ids + settings.telegram.admin_ids,
            bots_allowed=False,
        )

        logger.info("Initializing aiogram handlers")

        aiogram_help_command_handler = aiogram_handlers.HelpCommandHandler(
            app_version=settings.app.version,
        )
        aiogram_dispatcher.message.register(
            aiogram_help_command_handler.process,
            *aiogram_help_command_handler.filters,
        )

        if isinstance(settings.media_handler, app_settings.SynchronousMediaHandlerSettings):
            aiogram_media_message_handler = aiogram_handlers.SynchronousMediaMessageHandler(
                recognition_service=recognition_service,
                bot=aiogram_bot,
            )
        elif isinstance(settings.media_handler, app_settings.TemporalioMediaHandlerSettings):
            if isinstance(settings.media_handler.audio_storage, app_settings.S3AudioStorageSettings):
                audio_storage_s3_client = aiobotocore_utils.S3Client(
                    session=aiobotocore_session.AioSession(),
                    endpoint_url=settings.media_handler.audio_storage.s3.endpoint_url,
                    access_key=settings.media_handler.audio_storage.s3.access_key,
                    secret_key=settings.media_handler.audio_storage.s3.secret_key,
                )
                lifecycle_shutdown_callbacks.append(
                    lifecycle_utils.Callback.from_dispose(
                        name="audio_storage_s3_client",
                        awaitable=audio_storage_s3_client.dispose(),
                    )
                )
                aiohttp_subsystem_readiness_callbacks.append(
                    aiohttp_utils.SubsystemReadinessCallback(
                        name="audio_storage_s3",
                        is_ready=audio_storage_s3_client.is_ready,
                    )
                )
                audio_storage_client = voice_clients.S3Storage(
                    s3_client=audio_storage_s3_client,
                    bucket_name=settings.media_handler.audio_storage.s3.bucket_name,
                )
            else:
                raise NotImplementedError(
                    f"Unsupported audio storage type: {settings.media_handler.audio_storage.type_name}"
                )
            audio_storage_temporal_client = await temporalio_client.Client.connect(
                target_host=settings.media_handler.temporalio.endpoint_url,
                namespace=settings.media_handler.temporalio.namespace,
                lazy=True,
            )

            async def audio_storage_temporal_client_is_ready() -> bool:
                try:
                    await audio_storage_temporal_client.service_client.check_health()
                except Exception:
                    return False
                return True

            aiohttp_subsystem_readiness_callbacks.append(
                aiohttp_utils.SubsystemReadinessCallback(
                    name="audio_storage_temporal",
                    is_ready=audio_storage_temporal_client_is_ready,
                )
            )
            aiogram_media_recognition_task_service = voice_services.TemporalRecognitionTask(
                audio_storage_client=audio_storage_client,
                temporal_client=audio_storage_temporal_client,
                temporal_task_queue=settings.media_handler.temporalio.task_queue,
                split_timeout_seconds=settings.media_handler.split_timeout_seconds,
                recognition_timeout_seconds=settings.media_handler.recognition_timeout_seconds,
                clean_up_timeout_seconds=settings.media_handler.clean_up_timeout_seconds,
            )
            aiogram_media_message_handler = aiogram_handlers.TaskMediaMessageHandler(
                recognition_task_service=aiogram_media_recognition_task_service,
                bot=aiogram_bot,
            )
            aiohttp_media_callback_handler = aiohttp_handlers.MediaCallbackHandler(
                recognition_task_service=aiogram_media_recognition_task_service,
                callback_processor=aiogram_media_message_handler.process_callback,
            )
            aiohttp_url_dispatcher.add_route(
                aiohttp_media_callback_handler.method,
                aiohttp_media_callback_handler.path,
                aiohttp_media_callback_handler.process,
            )
        else:
            raise NotImplementedError(f"Unsupported media handler type: {settings.media_handler.type_name}")

        aiogram_dispatcher.message.register(
            aiogram_media_message_handler.process,
            aiogram_allowed_users_filter,
            *aiogram_media_message_handler.filters,
        )

        aiogram_lifecycle = aiogram_utils.Lifecycle(
            dispatcher=aiogram_dispatcher,
            bot=aiogram_bot,
            logger=logger,
            name=settings.telegram.bot_name,
            description=settings.telegram.bot_description,
            short_description=settings.telegram.bot_short_description,
            commands=[
                *aiogram_help_command_handler.bot_commands,
            ],
            webhook=(
                aiogram_utils.Lifecycle.Webhook(
                    url=f"{settings.server.public_host}{settings.telegram.webhook_url}",
                    secret_token=settings.telegram.webhook_secret_token,
                )
                if settings.telegram.webhook_enabled
                else None
            ),
        )
        lifecycle_startup_callbacks.extend(aiogram_lifecycle.get_startup_callbacks())
        lifecycle_shutdown_callbacks.extend(aiogram_lifecycle.get_shutdown_callbacks())
        if not settings.telegram.webhook_enabled:
            lifecycle_main_tasks.append(aiogram_lifecycle.get_main_task())

        logger.info("Initializing aiohttp middlewares")

        logger.info("Initializing aiohttp handlers")

        aiohttp_liveness_probe_handler = aiohttp_utils.LivenessProbeHandler()
        aiohttp_url_dispatcher.add_route("GET", "/api/v1/health/liveness", aiohttp_liveness_probe_handler.process)

        aiohttp_readiness_probe_handler = aiohttp_utils.ReadinessProbeHandler(
            subsystems=aiohttp_subsystem_readiness_callbacks,
        )
        aiohttp_url_dispatcher.add_route("GET", "/api/v1/health/readiness", aiohttp_readiness_probe_handler.process)

        if settings.telegram.webhook_enabled:
            aiohttp_telegram_webhook_handler = aiogram_aiohttp_webhook.SimpleRequestHandler(
                bot=aiogram_bot,
                dispatcher=aiogram_dispatcher,
                secret_token=settings.telegram.webhook_secret_token,
            )
            aiohttp_url_dispatcher.add_route(
                "POST",
                settings.telegram.webhook_url,
                aiohttp_telegram_webhook_handler.handle,
            )

        logger.info("Initializing aiohttp application")

        aiohttp_app = aiohttp_web.Application(
            middlewares=aiohttp_middlewares,
            router=aiohttp_url_dispatcher,
        )
        lifecycle_main_tasks.append(
            asyncio.create_task(
                coro=aiohttp_web._run_app(  # pyright: ignore[reportPrivateUsage]
                    app=aiohttp_app,
                    host=settings.server.host,
                    port=settings.server.port,
                    print=aiohttp_utils.PrintLogger(),
                ),
                name="aiohttp_app",
            )
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
