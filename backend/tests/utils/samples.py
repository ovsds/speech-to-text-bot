import lib.voice.models as voice_models


def get_voice_sample_path(format: voice_models.AudioFormat) -> str:
    return f"tests/data/voice/RU_F_DashaCH.{format.value}"


def read_voice_sample(format: voice_models.AudioFormat) -> voice_models.Audio:
    with open(get_voice_sample_path(format), "rb") as f:
        return voice_models.Audio(
            data=f.read(),
            duration_seconds=1,
            format=format,
        )


def write_voice_sample(audio: voice_models.Audio) -> None:
    with open(get_voice_sample_path(audio.format), "wb") as f:
        f.write(audio.data)


__all__ = [
    "read_voice_sample",
    "write_voice_sample",
]
