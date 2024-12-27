import asyncio
import concurrent.futures as concurrent_futures

import pytest

import lib.voice.clients as voice_clients
import lib.voice.models as voice_models
import tests.utils as tests_utils


@pytest.mark.asyncio
async def test_recognize_default():
    client = voice_clients.SpeechRecognitionClient(
        loop=asyncio.get_running_loop(),
        thread_pool_executor=concurrent_futures.ThreadPoolExecutor(max_workers=1),
    )

    audio = tests_utils.read_voice_sample(voice_models.AudioFormat.WAV)

    result = await client.recognize(audio)
    assert (
        result.text
        == "очень важен для нас оставайтесь на линии и вам ответит первый освободившийся оператор Напоминаем что вы можете сделать заказ на нашем сайте"
    )
    assert result.audio == audio
