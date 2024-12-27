import os
import tempfile
import typing
import uuid


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


__all__ = [
    "TempFile",
]
