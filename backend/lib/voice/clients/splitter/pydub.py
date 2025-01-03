import asyncio
import concurrent.futures as concurrent_futures
import dataclasses
import logging
import typing

import pydub
import pydub.silence as pydub_silence

import lib.utils.pydub as pydub_utils
import lib.voice.clients.conversion as voice_conversion_clients
import lib.voice.models as voice_models

MILLISECONDS_IN_SECOND = 1000

logger = logging.getLogger(__name__)


@dataclasses.dataclass(frozen=True)
class PydubOnSilenceSplitterClient:
    loop: asyncio.AbstractEventLoop
    thread_pool_executor: concurrent_futures.ThreadPoolExecutor
    conversion_client: voice_conversion_clients.ConversionClientProtocol

    min_silence_length_ms: int = 800
    silence_difference_db: int = 20
    chunk_beginning_silence_ms: int = 2000

    async def split(self, audio: voice_models.Audio) -> typing.AsyncIterator[voice_models.Audio]:
        audio = await self.conversion_client.convert(audio, voice_models.AudioFormat.WAV)
        splitted = await self.loop.run_in_executor(self.thread_pool_executor, self._split, audio)

        for item in splitted:
            yield item

    def _split(self, audio: voice_models.Audio) -> list[voice_models.Audio]:
        assert audio.format == voice_models.AudioFormat.WAV

        logger.debug(
            "Splitting audio, length(bytes)=%s, duration=%s",
            len(audio.data),
            audio.duration_seconds,
        )

        source_audio_segment = pydub_utils.get_audio_segment_from_data(
            data=audio.data,
            format=audio.format.to_pydub_format(),
        )

        chunks = typing.cast(
            typing.Sequence[pydub.AudioSegment],
            pydub_silence.split_on_silence(
                source_audio_segment,
                min_silence_len=self.min_silence_length_ms,
                silence_thresh=int(source_audio_segment.dBFS - self.silence_difference_db),
                keep_silence=self.chunk_beginning_silence_ms,
            ),
        )

        return [
            voice_models.Audio(
                data=pydub_utils.get_data_from_audio_segment(
                    audio_segment=chunk,
                    format=audio.format.to_pydub_format(),
                ),
                format=audio.format,
                duration_seconds=typing.cast(float, chunk.duration_seconds),
            )
            for chunk in chunks
        ]


__all__ = [
    "PydubOnSilenceSplitterClient",
]
