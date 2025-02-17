import dataclasses
import logging
import typing
import uuid

import aiogram
import aiogram.filters as aiogram_filters
import aiogram.types as aiogram_types

import lib.utils.aiogram as aiogram_utils
import lib.utils.pydantic as pydantic_utils
import lib.voice.models as voice_models
import lib.voice.services as voice_services

logger = logging.getLogger(__name__)


AUDIO_MIME_TYPE_TO_FORMAT = {
    "audio/ogg": voice_models.AudioFormat.OGG,
    "audio/mpeg": voice_models.AudioFormat.MP3,
    "audio/x-wav": voice_models.AudioFormat.WAV,
    "video/mp4": voice_models.AudioFormat.MP4,
}

TELEGRAM_MESSAGE_MAX_LENGTH = 4096


@dataclasses.dataclass(frozen=True)
class BaseMediaMessageHandler:
    bot: aiogram.Bot

    async def _download_file_data(self, file_id: str) -> bytes:
        file = await self.bot.get_file(file_id)

        assert file.file_path is not None
        file_bites_io = await self.bot.download_file(file.file_path)

        assert file_bites_io is not None
        return file_bites_io.read()

    def _meme_type_to_audio_format(self, mime_type: str | None) -> voice_models.AudioFormat:
        if mime_type is None:
            raise ValueError("Mime type is None")

        if mime_type not in AUDIO_MIME_TYPE_TO_FORMAT:
            raise ValueError(f"Unsupported audio mime type: {mime_type}")

        return AUDIO_MIME_TYPE_TO_FORMAT[mime_type]

    async def _get_voice_audio(self, message_voice: aiogram_types.Voice) -> voice_models.Audio:
        data = await self._download_file_data(message_voice.file_id)

        return voice_models.Audio(
            data=data,
            duration_seconds=message_voice.duration,
            format=voice_models.AudioFormat.OGG,
        )

    async def _get_audio_audio(self, message_audio: aiogram_types.Audio) -> voice_models.Audio:
        data = await self._download_file_data(message_audio.file_id)
        format = self._meme_type_to_audio_format(message_audio.mime_type)

        return voice_models.Audio(
            data=data,
            duration_seconds=message_audio.duration,
            format=format,
        )

    async def _get_document_audio(self, message_document: aiogram_types.Document) -> voice_models.Audio:
        data = await self._download_file_data(message_document.file_id)
        format = self._meme_type_to_audio_format(message_document.mime_type)

        return voice_models.Audio(
            data=data,
            duration_seconds=0,
            format=format,
        )

    async def _get_video_audio(self, message_video: aiogram_types.Video) -> voice_models.Audio:
        data = await self._download_file_data(message_video.file_id)
        format = self._meme_type_to_audio_format(message_video.mime_type)

        return voice_models.Audio(
            data=data,
            duration_seconds=message_video.duration,
            format=format,
        )

    async def _get_video_note_audio(self, message_video_note: aiogram_types.VideoNote) -> voice_models.Audio:
        data = await self._download_file_data(message_video_note.file_id)

        return voice_models.Audio(
            data=data,
            duration_seconds=message_video_note.duration,
            format=voice_models.AudioFormat.MP4,
        )

    async def _get_message_audio(self, message: aiogram_types.Message) -> voice_models.Audio:
        if message.voice is not None:
            return await self._get_voice_audio(message.voice)
        elif message.audio is not None:
            return await self._get_audio_audio(message.audio)
        elif message.document is not None:
            return await self._get_document_audio(message.document)
        elif message.video_note is not None:
            return await self._get_video_note_audio(message.video_note)
        elif message.video is not None:
            return await self._get_video_audio(message.video)

        raise ValueError("Unsupported message content type")

    @property
    def filters(self) -> typing.Sequence[aiogram_filters.Filter]:
        return [
            aiogram_filters.or_f(
                aiogram_utils.ContentTypeMessageFilter(content_type=aiogram_types.ContentType.VOICE),
                aiogram_utils.ContentTypeMessageFilter(content_type=aiogram_types.ContentType.AUDIO),
                aiogram_utils.ContentTypeMessageFilter(content_type=aiogram_types.ContentType.DOCUMENT),
                aiogram_utils.ContentTypeMessageFilter(content_type=aiogram_types.ContentType.VIDEO_NOTE),
                aiogram_utils.ContentTypeMessageFilter(content_type=aiogram_types.ContentType.VIDEO),
            )
        ]

    def _get_timer_prefix(self, start: float, end: float) -> str:
        start_minutes = int(start // 60)
        start_seconds = int(start % 60)
        end_minutes = int(end // 60)
        end_seconds = int(end % 60)

        return f"{start_minutes:02}:{start_seconds:02} - {end_minutes:02}:{end_seconds:02}"

    async def _send_result(
        self,
        send_message_callback: typing.Callable[[str], typing.Awaitable[aiogram_types.Message]],
        recognition_results: typing.AsyncIterator[voice_models.RecognitionResult],
    ) -> None:
        time_passed = 0
        last_sent_message: aiogram_types.Message | None = None

        async for chunk in recognition_results:
            chunk_prefix = self._get_timer_prefix(
                start=time_passed,
                end=time_passed + chunk.duration_seconds,
            )
            chunk_text = f"{chunk_prefix}: {chunk.text}"

            if (
                last_sent_message is not None
                and last_sent_message.text is not None
                and len(chunk_text) + len(last_sent_message.text) > TELEGRAM_MESSAGE_MAX_LENGTH
            ):
                last_sent_message = None

            if last_sent_message is None:
                last_sent_message = await send_message_callback(chunk_text)
            else:
                edit_result = await last_sent_message.edit_text(text=f"{last_sent_message.text}\n{chunk_text}")
                assert isinstance(edit_result, aiogram_types.Message)
                last_sent_message = edit_result

            time_passed += chunk.duration_seconds


@dataclasses.dataclass(frozen=True)
class SynchronousMediaMessageHandler(BaseMediaMessageHandler):
    recognition_service: voice_services.RecognitionProtocol

    async def process(self, message: aiogram_types.Message):
        logger.info("Processing message content type: %s", message.content_type)
        audio = await self._get_message_audio(message)
        recognition_results = self.recognition_service.recognize(audio)

        await self._send_result(
            send_message_callback=message.reply,
            recognition_results=recognition_results,
        )


@dataclasses.dataclass(frozen=True)
class TaskMediaMessageHandler(BaseMediaMessageHandler):
    recognition_task_service: voice_services.RecognitionTaskProtocol

    class MetadataSchema(pydantic_utils.BaseSchema):
        message_id: int
        message_chat_id: int
        message_thread_id: int | None
        message_business_connection_id: str | None

    async def process(self, message: aiogram_types.Message):
        logger.info("Processing message content type: %s", message.content_type)
        audio = await self._get_message_audio(message)

        metadata = self.MetadataSchema(
            message_id=message.message_id,
            message_chat_id=message.chat.id,
            message_thread_id=message.message_thread_id if message.is_topic_message else None,
            message_business_connection_id=message.business_connection_id,
        )

        await self.recognition_task_service.add_task(
            audio=audio,
            task_metadata=metadata.to_json_str(),
        )

    async def process_callback(
        self,
        audio_id: uuid.UUID,
    ) -> None:
        result = await self.recognition_task_service.get_result(audio_id=audio_id)
        metadata = self.MetadataSchema.from_json_str(result.metadata)

        async def send_message_callback(text: str) -> aiogram_types.Message:
            return await self.bot.send_message(
                text=text,
                chat_id=metadata.message_chat_id,
                message_thread_id=metadata.message_thread_id,
                business_connection_id=metadata.message_business_connection_id,
                reply_parameters=aiogram_types.ReplyParameters(
                    message_id=metadata.message_id,
                    chat_id=metadata.message_chat_id,
                ),
            )

        async def recognition_results_generator() -> typing.AsyncIterator[voice_models.RecognitionResult]:
            for recognition_results in result.recognition_results:
                yield recognition_results

        await self._send_result(
            send_message_callback=send_message_callback,
            recognition_results=recognition_results_generator(),
        )


__all__ = [
    "SynchronousMediaMessageHandler",
    "TaskMediaMessageHandler",
]
