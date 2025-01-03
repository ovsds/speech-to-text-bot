import asyncio
import concurrent.futures as concurrent_futures
import dataclasses
import logging
import typing

import lib.utils.pydub as pydub_utils
import lib.voice.models as voice_models

logger = logging.getLogger(__name__)


@dataclasses.dataclass(frozen=True)
class PydubConversionClient:
    loop: asyncio.AbstractEventLoop
    thread_pool_executor: concurrent_futures.ThreadPoolExecutor

    async def convert(self, audio: voice_models.Audio, format: voice_models.AudioFormat) -> voice_models.Audio:
        return await self.loop.run_in_executor(self.thread_pool_executor, self._convert, audio, format)

    def _convert(self, audio: voice_models.Audio, format: voice_models.AudioFormat) -> voice_models.Audio:
        if audio.format == format:
            return audio

        logger.debug(
            "Converting audio from %s to %s, length(bytes)=%s, duration=%s",
            audio.format,
            format,
            len(audio.data),
            audio.duration_seconds,
        )

        source = pydub_utils.get_audio_segment_from_data(
            data=audio.data,
            format=audio.format.to_pydub_format(),
        )

        result_data = pydub_utils.get_data_from_audio_segment(
            audio_segment=source,
            format=format.to_pydub_format(),
        )

        return voice_models.Audio(
            data=result_data,
            duration_seconds=typing.cast(float, source.duration_seconds),
            format=format,
        )


__all__ = [
    "PydubConversionClient",
]
