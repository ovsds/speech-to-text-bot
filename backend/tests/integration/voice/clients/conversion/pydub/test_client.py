import asyncio
import concurrent.futures as concurrent_futures

import pytest

import lib.voice.clients as voice_clients
import lib.voice.models as voice_models
import tests.utils as tests_utils


@pytest.mark.parametrize(
    "source_format",
    list(voice_models.AudioFormat),
)
@pytest.mark.parametrize(
    "target_format",
    list(voice_models.AudioFormat),
)
@pytest.mark.asyncio
async def test_convert_default(
    source_format: voice_models.AudioFormat,
    target_format: voice_models.AudioFormat,
) -> None:
    source_audio = tests_utils.read_voice_sample(source_format)

    client = voice_clients.PydubConversionClient(
        loop=asyncio.get_running_loop(),
        thread_pool_executor=concurrent_futures.ThreadPoolExecutor(max_workers=1),
    )
    await client.convert(
        audio=source_audio,
        format=target_format,
    )
