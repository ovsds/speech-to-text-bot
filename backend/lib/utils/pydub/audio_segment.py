import enum
import os
import tempfile
import typing
import uuid

import pydub


class AudioSegmentFormat(enum.Enum):
    MP3 = "mp3"
    MP4 = "mp4"
    OGG = "ogg"
    WAV = "wav"


class TempFile:
    def __init__(self):
        self._path = os.path.join(tempfile.gettempdir(), str(uuid.uuid4()))

    def __enter__(self):
        return self

    def __exit__(self, *_args: typing.Any, **_kwargs: typing.Any):
        try:
            os.remove(self._path)
        except FileNotFoundError:
            pass

    def read(self) -> bytes:
        with open(self._path, "rb") as file:
            return file.read()

    def write(self, data: bytes):
        with open(self._path, "wb") as file:
            file.write(data)

    @property
    def path(self) -> str:
        return self._path


def get_audio_segment_from_data(data: bytes, format: AudioSegmentFormat) -> pydub.AudioSegment:
    with TempFile() as temp_file:
        temp_file.write(data)
        return typing.cast(
            pydub.AudioSegment,
            pydub.AudioSegment.from_file(file=temp_file.path, format=format.value),
        )


def get_data_from_audio_segment(audio_segment: pydub.AudioSegment, format: AudioSegmentFormat) -> bytes:
    with TempFile() as temp_file:
        temp_file_path = temp_file.path
        audio_segment.export(temp_file_path, format.value)
        return temp_file.read()


__all__ = [
    "AudioSegmentFormat",
    "get_audio_segment_from_data",
    "get_data_from_audio_segment",
]
