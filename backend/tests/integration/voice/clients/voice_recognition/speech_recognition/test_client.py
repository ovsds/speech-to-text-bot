import asyncio
import concurrent.futures as concurrent_futures

import pytest
import pytest_mock

import lib.voice.clients as voice_clients
import lib.voice.models as voice_models
import tests.utils as tests_utils


@pytest.mark.asyncio
async def test_recognize_default(
    mocker: pytest_mock.MockFixture,
):
    audio = tests_utils.read_voice_sample(voice_models.AudioFormat.WAV)

    conversion_client = mocker.MagicMock(spec=voice_clients.ConversionClientProtocol)
    conversion_client.convert.return_value = audio

    client = voice_clients.SpeechRecognitionClient(
        loop=asyncio.get_running_loop(),
        thread_pool_executor=concurrent_futures.ThreadPoolExecutor(max_workers=1),
        conversion_client=conversion_client,
    )

    result = await client.recognize(audio)
    assert (
        result.text
        == "очень важен для нас оставайтесь на линии и вам ответит первый освободившийся оператор Напоминаем что вы можете сделать заказ на нашем сайте"
    )
    assert result.audio == audio
