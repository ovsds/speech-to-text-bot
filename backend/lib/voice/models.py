import dataclasses
import enum

import lib.utils.pydub as pydub_utils


class AudioFormat(enum.Enum):
    MP3 = "mp3"
    MP4 = "mp4"
    OGG = "ogg"
    WAV = "wav"

    def to_pydub_format(self) -> pydub_utils.AudioSegmentFormat:
        return _PYDUB_MAP[self]


_PYDUB_MAP: dict[AudioFormat, pydub_utils.AudioSegmentFormat] = {
    AudioFormat.MP3: pydub_utils.AudioSegmentFormat.MP3,
    AudioFormat.MP4: pydub_utils.AudioSegmentFormat.MP4,
    AudioFormat.OGG: pydub_utils.AudioSegmentFormat.OGG,
    AudioFormat.WAV: pydub_utils.AudioSegmentFormat.WAV,
}


@dataclasses.dataclass
class Audio:
    data: bytes
    duration_seconds: float
    format: AudioFormat


@dataclasses.dataclass
class RecognitionResult:
    text: str
    audio: Audio


__all__ = ["Audio", "AudioFormat"]
