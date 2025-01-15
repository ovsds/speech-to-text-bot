import aiobotocore.session as aiobotocore_session
import pytest

import lib.utils.aiobotocore as aiobotocore_utils
import tests.settings as test_settings


@pytest.fixture(name="s3_client")
def fixture_s3_client(
    settings: test_settings.Settings,
):
    return aiobotocore_utils.S3Client(
        session=aiobotocore_session.AioSession(),
        endpoint_url=settings.s3.endpoint_url,
        access_key=settings.s3.access_key,
        secret_key=settings.s3.secret_key,
    )
