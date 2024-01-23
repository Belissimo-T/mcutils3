from __future__ import annotations

import abc
import dataclasses
import itertools
import typing

from .errors import CompilationError


class StringResolver:
    def __init__(self):
        self.strings: dict[String, str] = {}
        self.strings_set: set[str] = set()

    def resolve_identifier(self, string: String) -> str:
        if string in self.strings:
            return self.strings[string]
        else:
            val = string.get_str(self.strings_set, self.resolve_identifier)
            self.strings[string] = val
            self.strings_set.add(val)
            return val


class String(abc.ABC):
    @abc.abstractmethod
    def get_str(self, existing_strings: set[str], resolve_string: typing.Callable[[String], str]) -> str:
        ...

    def __hash__(self):
        return hash(id(self))

    def __eq__(self, other):
        return id(self) == id(other)


class LiteralString(String):
    def __init__(self, literal: str, *args: String | str):
        self.literal = literal
        self.args = args

    def get_str(self, existing_strings: set[str], resolve_string: typing.Callable[[String], str]) -> str:
        format_args = tuple(map(resolve_string, self.args))

        try:
            return self.literal % format_args
        except TypeError as e:
            raise CompilationError(f"Command {self.literal!r} has {len(self.args)} args.") from e


@dataclasses.dataclass(frozen=True)
class UniqueString(String, abc.ABC):
    string: String

    counter: typing.Iterable[typing.Callable[[str], str]] = dataclasses.field(
        default_factory=lambda: ((lambda x, __n=n: x + __n) for n in map(str, itertools.count(2))))

    def get_str(self, existing_strings: set[str], resolve_string: typing.Callable[[String], str]) -> str:
        val = resolve_string(self.string)

        for counter in itertools.chain([lambda x: x], self.counter):
            new_val = counter(val)

            if new_val not in existing_strings:
                return new_val


@dataclasses.dataclass(frozen=True)
class RestrictedUniqueIdentifier(UniqueString):
    string: String
    # pattern = re.compile(r"^[a-zA-Z0-9_+\-.]+$")


class UniqueTag(UniqueString): pass


class UniqueScoreboardObjective(UniqueString): pass


class UniqueScoreboardPlayer(UniqueString): pass


@dataclasses.dataclass(frozen=True)
class Comment(String):
    comment: str

    def get_str(self, existing_strings: set[str], resolve_string: typing.Callable[[String], str]) -> str:
        return f"# {self.comment}"
