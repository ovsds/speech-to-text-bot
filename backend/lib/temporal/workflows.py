import asyncio
import dataclasses
import datetime
import logging
import typing
import uuid

import temporalio.workflow as temporalio_workflow

with temporalio_workflow.unsafe.imports_passed_through():
    import lib.temporal.activities as temporal_activities
    import lib.voice.models as voice_models


logger = logging.getLogger(__name__)

T = typing.TypeVar("T")


@temporalio_workflow.defn
class Recognition:
    def __init__(self) -> None:
        self.result: voice_models.RecognitionTaskResult | None = None

    async def _split(
        self,
        audio_id: uuid.UUID,
        timeout: datetime.timedelta,
    ) -> list[uuid.UUID]:
        return await temporalio_workflow.execute_activity(
            temporal_activities.Splitter.name,
            temporal_activities.Splitter.Params(audio_id),
            start_to_close_timeout=datetime.timedelta(seconds=60),
        )

    async def _recognize(
        self,
        audio_ids: list[uuid.UUID],
        timeout: datetime.timedelta,
    ) -> list[voice_models.RecognitionResult]:
        return await asyncio.gather(
            *[
                temporalio_workflow.execute_activity(
                    temporal_activities.Recognition.name,
                    temporal_activities.Recognition.Params(id),
                    start_to_close_timeout=datetime.timedelta(seconds=60),
                )
                for id in audio_ids
            ]
        )

    async def _clean_up(self, audio_ids: list[uuid.UUID], timeout: datetime.timedelta) -> None:
        await asyncio.gather(
            *[
                temporalio_workflow.execute_activity(
                    temporal_activities.Cleaner.name,
                    temporal_activities.Cleaner.Params(id),
                    start_to_close_timeout=timeout,
                )
                for id in audio_ids
            ]
        )

    async def _callback(self, audio_id: uuid.UUID, timeout: datetime.timedelta) -> None:
        await temporalio_workflow.execute_activity(
            temporal_activities.Callback.name,
            temporal_activities.Callback.Params(audio_id),
            start_to_close_timeout=timeout,
        )

    @temporalio_workflow.query
    def get_result(self) -> voice_models.RecognitionTaskResult | None:
        return self.result

    @dataclasses.dataclass(frozen=True)
    class Params:
        metadata: str

        audio_id: uuid.UUID
        split_timeout_seconds: int = 10 * 60
        recognize_timeout_seconds: int = 10 * 60
        clean_up_timeout_seconds: int = 60
        callback_timeout_seconds: int = 10

        @property
        def split_timeout(self) -> datetime.timedelta:
            return datetime.timedelta(seconds=self.split_timeout_seconds)

        @property
        def recognize_timeout(self) -> datetime.timedelta:
            return datetime.timedelta(seconds=self.recognize_timeout_seconds)

        @property
        def clean_up_timeout(self) -> datetime.timedelta:
            return datetime.timedelta(seconds=self.clean_up_timeout_seconds)

        @property
        def callback_timeout(self) -> datetime.timedelta:
            return datetime.timedelta(seconds=self.callback_timeout_seconds)

    @temporalio_workflow.run
    async def run(self, params: Params) -> voice_models.RecognitionTaskResult:
        audio_id = params.audio_id

        splitted_ids = await self._split(audio_id=audio_id, timeout=params.split_timeout)
        recognition_results = await self._recognize(audio_ids=[*splitted_ids], timeout=params.recognize_timeout)
        self.result = voice_models.RecognitionTaskResult(
            recognition_results=recognition_results,
            metadata=params.metadata,
        )

        await self._callback(audio_id=audio_id, timeout=params.callback_timeout)
        await self._clean_up(audio_ids=[audio_id, *splitted_ids], timeout=params.clean_up_timeout)

        return self.result


__all__ = [
    "Recognition",
]
