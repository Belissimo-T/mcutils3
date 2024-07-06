import dataclasses
import typing
import nbtlib

from . import strings
from .errors import CompilationError
from .strings import String

NbtPyData = typing.Union[
    int,
    float,
    str,
    # bytes,
    list["NbtPyData"],
    dict[str, "NbtPyData"]
]


def convert_python_to_nbtlib(data: NbtPyData) -> nbtlib.Base:
    match data:
        case int():
            return nbtlib.Int(data)
        case float():
            return nbtlib.Double(data)
        case str():
            return nbtlib.String(data)
        case list():
            return nbtlib.List([convert_python_to_nbtlib(x) for x in data])
        case dict():
            return nbtlib.Compound({k: convert_python_to_nbtlib(v) for k, v in data.items()})
        case _:
            raise CompilationError(f"Can't serialize python value {data!r} of type {type(data)} to NBT.")


def dumps(data: NbtPyData) -> str:
    tag = convert_python_to_nbtlib(data)

    try:
        return nbtlib.serialize_tag(tag, indent=None, compact=False)
    except Exception as e:
        raise CompilationError(f"Error serializing NBT from {data!r}.") from e


@dataclasses.dataclass
class NbtString(strings.String):
    data: NbtPyData

    def get_str(
        self,
        existing_strings: dict[str, set[str]],
        resolve_string: typing.Callable[[String], str]
    ) -> tuple[str, str]:
        return dumps(self.data), "snbt"
