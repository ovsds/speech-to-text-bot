import uuid

import aiobotocore.session as aiobotocore_session
import pytest

import lib.utils.aiobotocore as aiobotocore_utils
import lib.voice.clients as voice_clients
import lib.voice.models as voice_models
import tests.settings as test_settings
import tests.utils as test_utils


@pytest.fixture(name="s3_storage_client")
def fixture_s3_storage_client(
    settings: test_settings.Settings,
):
    return voice_clients.S3Storage(
        s3_client=aiobotocore_utils.S3Client(
            client_context=aiobotocore_utils.S3ClientContext(
                session=aiobotocore_session.AioSession(),
                endpoint_url=settings.s3.endpoint_url,
                access_key=settings.s3.access_key,
                secret_key=settings.s3.secret_key,
            ),
        ),
        bucket_name=settings.s3.bucket_name,
    )


@pytest.fixture(name="audio")
def fixture_audio():
    return test_utils.read_voice_sample(format=voice_models.AudioFormat.WAV)


@pytest.mark.asyncio
async def test_create_read_delete(
    s3_storage_client: voice_clients.S3Storage,
    audio: voice_models.Audio,
):
    audio_id = uuid.uuid4()

    await s3_storage_client.create(audio_id, audio)
    stored_audio = await s3_storage_client.read(audio_id)
    await s3_storage_client.delete(audio_id)

    assert audio == stored_audio


@pytest.mark.asyncio
async def test_read_not_found_raises(
    s3_storage_client: voice_clients.S3Storage,
):
    audio_id = uuid.uuid4()

    with pytest.raises(voice_clients.StorageProtocol.NotFoundError):
        await s3_storage_client.read(audio_id)


@pytest.mark.asyncio
async def test_delete_not_found_succeeds(
    s3_storage_client: voice_clients.S3Storage,
):
    audio_id = uuid.uuid4()

    await s3_storage_client.delete(audio_id)


@pytest.mark.asyncio
async def test_create_already_exists_raises(
    s3_storage_client: voice_clients.S3Storage,
    audio: voice_models.Audio,
):
    audio_id = uuid.uuid4()

    await s3_storage_client.create(audio_id, audio)

    with pytest.raises(voice_clients.StorageProtocol.AlreadyExistsError):
        await s3_storage_client.create(audio_id, audio)
