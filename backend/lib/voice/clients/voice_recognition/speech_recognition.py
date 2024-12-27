import asyncio
import concurrent.futures as concurrent_futures
import dataclasses
import io
import typing

import speech_recognition

import lib.voice.models as voice_models


@dataclasses.dataclass(frozen=True)
class SpeechRecognitionClient:
    loop: asyncio.AbstractEventLoop
    thread_pool_executor: concurrent_futures.ThreadPoolExecutor

    async def recognize(self, audio: voice_models.Audio) -> voice_models.RecognitionResult:
        return await self.loop.run_in_executor(self.thread_pool_executor, self._recognize, audio)

    def _recognize(self, audio: voice_models.Audio) -> voice_models.RecognitionResult:
        assert audio.format == voice_models.AudioFormat.WAV

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
            audio=audio,
        )


__all__ = [
    "SpeechRecognitionClient",
]
