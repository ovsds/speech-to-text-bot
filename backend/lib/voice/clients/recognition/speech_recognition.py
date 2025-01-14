import asyncio
import concurrent.futures as concurrent_futures
import dataclasses
import io
import logging
import typing

import speech_recognition

import lib.voice.clients.conversion as voice_conversion_clients
import lib.voice.models as voice_models

logger = logging.getLogger(__name__)


@dataclasses.dataclass(frozen=True)
class SpeechRecognition:
    loop: asyncio.AbstractEventLoop
    thread_pool_executor: concurrent_futures.ThreadPoolExecutor
    conversion_client: voice_conversion_clients.ConversionProtocol

    async def recognize(self, audio: voice_models.Audio) -> voice_models.RecognitionResult:
        audio = await self.conversion_client.convert(audio, voice_models.AudioFormat.WAV)
        return await self.loop.run_in_executor(self.thread_pool_executor, self._recognize, audio)

    def _recognize(self, audio: voice_models.Audio) -> voice_models.RecognitionResult:
        logger.debug("Recognizing audio, length(bytes)=%s, duration=%s", len(audio.data), audio.duration_seconds)

        audio_io = io.BytesIO(audio.data)
        recognizer = speech_recognition.Recognizer()

        with speech_recognition.AudioFile(audio_io) as source:
            recognizer.adjust_for_ambient_noise(source)
            audio_data = recognizer.record(source)

        try:
            result = typing.cast(str, recognizer.recognize_google(audio_data, language="ru"))
        except speech_recognition.UnknownValueError:
            result = "UNRECOGNIZED"

        return voice_models.RecognitionResult(
            text=result,
            duration_seconds=audio.duration_seconds,
        )


__all__ = [
    "SpeechRecognition",
]
