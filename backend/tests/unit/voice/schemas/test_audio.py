import lib.voice.models as voice_models
import lib.voice.schemas as voice_schemas
import tests.utils as test_utils


def test_serialize_deserialize():
    before_audio = test_utils.read_voice_sample(format=voice_models.AudioFormat.WAV)

    before_audio_schema = voice_schemas.Audio.from_dataclass(before_audio)
    raw_audio = before_audio_schema.to_bytes()
    after_audio_schema = voice_schemas.Audio.from_bytes(raw_audio)
    after_audio = after_audio_schema.to_dataclass()

    assert before_audio == after_audio
