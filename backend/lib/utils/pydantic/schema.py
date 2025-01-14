import dataclasses
import enum
import typing

import msgpack

import lib.utils.json as json_utils
import lib.utils.pydantic.base as base


def default(data: typing.Any) -> typing.Any:
    if isinstance(data, enum.Enum):
        return data.value

    return data


DATACLASS_T = typing.TypeVar("DATACLASS_T")


class BaseSchema(base.BaseModel):
    @classmethod
    def from_bytes(cls, data: bytes) -> typing.Self:
        raw_data = msgpack.loads(data)
        return cls.model_validate(raw_data)

    def to_bytes(self) -> bytes:
        raw_data = self.model_dump()
        return msgpack.dumps(raw_data, default=default)

    @classmethod
    def from_json_bytes(cls, data: bytes) -> typing.Self:
        raw_data = json_utils.loads_bytes(data)
        return cls.model_validate(raw_data)

    def to_json_bytes(self) -> bytes:
        raw_data = self.model_dump()
        return json_utils.dumps_bytes(raw_data)

    @classmethod
    def from_json_str(cls, data: str) -> typing.Self:
        raw_data = json_utils.loads_str(data)
        return cls.model_validate(raw_data)

    def to_json_str(self) -> str:
        raw_data = self.model_dump()
        return json_utils.dumps_str(raw_data)


class BaseDataclassSchema(BaseSchema, typing.Generic[DATACLASS_T]):
    class Meta:
        DATACLASS: type = NotImplemented

    @classmethod
    def from_dataclass(cls, data: DATACLASS_T) -> typing.Self:
        assert dataclasses.is_dataclass(data) and not isinstance(data, type)
        raw_data = dataclasses.asdict(data)
        return cls(**raw_data)

    def to_dataclass(self) -> DATACLASS_T:
        raw_data = self.model_dump()
        return self.Meta.DATACLASS(**raw_data)


__all__ = [
    "BaseDataclassSchema",
    "BaseSchema",
]
