import asyncio
import concurrent.futures as concurrent_futures

import pytest

import lib.voice.clients as voice_clients
import lib.voice.models as voice_models
import lib.voice.services as voice_services
import tests.utils as test_utils


@pytest.mark.asyncio
async def test_default():
    loop = asyncio.get_running_loop()
    thread_pool_executor = concurrent_futures.ThreadPoolExecutor(max_workers=1)

    conversion_client = voice_clients.PydubConversion(
        loop=loop,
        thread_pool_executor=thread_pool_executor,
    )
    splitter_client = voice_clients.PydubOnSilenceSplitter(
        loop=loop,
        thread_pool_executor=thread_pool_executor,
        conversion_client=conversion_client,
    )
    recognition_client = voice_clients.SpeechRecognition(
        loop=loop,
        thread_pool_executor=thread_pool_executor,
        conversion_client=conversion_client,
    )

    service = voice_services.Recognition(
        splitter_client=splitter_client,
        recognition_client=recognition_client,
    )

    audio = test_utils.read_voice_sample(voice_models.AudioFormat.OGG)
    expected = "очень важен для нас оставайтесь на линии и вам ответит первый освободившийся оператор Напоминаем что вы можете сделать заказ на нашем сайте"

    async for item in service.recognize(audio):
        assert item.text == expected
