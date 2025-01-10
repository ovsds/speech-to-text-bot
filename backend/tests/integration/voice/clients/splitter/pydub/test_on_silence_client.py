import asyncio
import concurrent.futures as concurrent_futures

import pytest
import pytest_mock

import lib.voice.clients as voice_clients
import lib.voice.models as voice_models
import tests.utils as test_utils


@pytest.mark.asyncio
async def test_split_on_silence_default(
    mocker: pytest_mock.MockFixture,
) -> None:
    source_audio = test_utils.read_voice_sample(voice_models.AudioFormat.WAV)

    conversion_client = mocker.MagicMock(spec=voice_clients.ConversionProtocol)
    conversion_client.convert.return_value = source_audio

    client = voice_clients.PydubOnSilenceSplitter(
        loop=asyncio.get_running_loop(),
        thread_pool_executor=concurrent_futures.ThreadPoolExecutor(max_workers=1),
        conversion_client=conversion_client,
        silence_difference_db=0,
    )

    count = 0
    async for chunk in client.split(source_audio):
        assert chunk.format == voice_models.AudioFormat.WAV
        assert chunk.duration_seconds > 0
        count += 1

    assert count == 3
