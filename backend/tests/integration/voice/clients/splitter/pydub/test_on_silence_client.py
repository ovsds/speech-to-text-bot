import asyncio
import concurrent.futures as concurrent_futures

import pytest

import lib.voice.clients as voice_clients
import lib.voice.models as voice_models
import tests.utils as tests_utils


@pytest.mark.asyncio
async def test_split_on_silence_default() -> None:
    source_audio = tests_utils.read_voice_sample(voice_models.AudioFormat.WAV)

    client = voice_clients.PydubOnSilenceSplitterClient(
        loop=asyncio.get_running_loop(),
        thread_pool_executor=concurrent_futures.ThreadPoolExecutor(max_workers=1),
        silence_difference_db=0,
    )

    chunks = await client.split(source_audio)

    assert len(chunks) == 3

    for chunk in chunks:
        assert chunk.format == voice_models.AudioFormat.WAV
        assert chunk.duration_seconds > 0
