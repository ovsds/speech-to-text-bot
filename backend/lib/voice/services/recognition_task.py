import dataclasses
import uuid

import temporalio.client as temporalio_client

import lib.temporal.workflows as temporal_workflows
import lib.voice.clients as voice_clients
import lib.voice.models as voice_models
import lib.voice.services.protocols as protocols


@dataclasses.dataclass(frozen=True)
class TemporalRecognitionTask(protocols.RecognitionTaskProtocol):
    audio_storage_client: voice_clients.StorageProtocol
    temporal_client: temporalio_client.Client
    temporal_task_queue: str
    split_timeout_seconds: int
    recognition_timeout_seconds: int
    clean_up_timeout_seconds: int

    async def add_task(
        self,
        audio: voice_models.Audio,
        task_metadata: str,
    ) -> None:
        audio_id = uuid.uuid4()
        await self.audio_storage_client.create(audio_id, audio)

        await self.temporal_client.start_workflow(
            temporal_workflows.Recognition.run,
            temporal_workflows.Recognition.Params(
                audio_id=audio_id,
                split_timeout_seconds=self.split_timeout_seconds,
                recognize_timeout_seconds=self.recognition_timeout_seconds,
                clean_up_timeout_seconds=self.clean_up_timeout_seconds,
                metadata=task_metadata,
            ),
            id=str(audio_id),
            task_queue=self.temporal_task_queue,
        )

    async def get_result(
        self,
        audio_id: uuid.UUID,
    ) -> voice_models.RecognitionTaskResult:
        workflow_handle = self.temporal_client.get_workflow_handle(
            workflow_id=str(audio_id),
            result_type=voice_models.RecognitionTaskResult,
        )
        result = await workflow_handle.query(
            temporal_workflows.Recognition.get_result,
        )
        assert result is not None
        return result


__all__ = [
    "TemporalRecognitionTask",
]
