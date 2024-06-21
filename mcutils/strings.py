from __future__ import annotations

import abc
import dataclasses
import itertools
import typing
from collections import defaultdict

from .errors import CompilationError

_ID = 0


class StringResolver:
    def __init__(self):
        self.strings: dict[String, str] = {}
        self.existing_strings: dict[str, set[str]] = defaultdict(set)

    def resolve_identifier(self, string: String) -> str:
        if string in self.strings:
            return self.strings[string]
        else:
            val, type_ = string.get_str(self.existing_strings, self.resolve_identifier)

            self.strings[string] = val
            self.existing_strings[type_].add(val)
            # print(f"Resolved {string} to {val!r}")
            return val


class String(abc.ABC):
    def __init__(self):
        global _ID
        self._id = _ID
        _ID += 1

    @abc.abstractmethod
    def get_str(
        self,
        existing_strings: dict[str, set[str]],
        resolve_string: typing.Callable[[String], str]
    ) -> tuple[str, str]:
        ...


class LiteralString(String):
    def __init__(self, literal: str, *args: String | str):
        if any(arg is None for arg in args):
            raise CompilationError("None in args.")

        super().__init__()
        self.literal = literal
        self.args = args

    def get_str(
        self,
        existing_strings: dict[str, set[str]],
        resolve_string: typing.Callable[[String], str]
    ) -> tuple[str, str]:
        format_args = tuple((arg if isinstance(arg, str) else resolve_string(arg)) for arg in self.args)

        try:
            return self.literal % format_args, "literal"
        except (TypeError, ValueError) as e:
            raise CompilationError(f"Command {self.literal!r} has {len(self.args)} args.") from e

    def __hash__(self):
        return hash((self.literal, self.args, self.__class__.__name__))

    def __eq__(self, other):
        if not isinstance(other, self.__class__):
            return False
        return self.literal == other.literal and self.args == other.args


@dataclasses.dataclass(frozen=True)
class _Counter:
    start: int = 2

    def __iter__(self):
        return (lambda x: x + str(i) for i in itertools.count(self.start))


@dataclasses.dataclass(frozen=True)
class UniqueString(String, abc.ABC):
    string: String
    category: str = dataclasses.field(init=False)

    counter: typing.Iterable[typing.Callable[[str], str]] = dataclasses.field(default_factory=_Counter)

    def __post_init__(self):
        String.__init__(self)
        # breakpoint()

    def get_str(
        self,
        existing_strings: dict[str, set[str]],
        resolve_string: typing.Callable[[String], str]
    ) -> tuple[str, str]:
        val = resolve_string(self.string)

        for counter in itertools.chain([lambda x: x], self.counter):
            new_val = counter(val)

            if new_val not in existing_strings[self.category]:
                return new_val, self.category

    def __hash__(self):
        return hash((self._id, self.__class__.__name__))

    def __eq__(self, other):
        if not isinstance(other, self.__class__):
            return False
        return self._id == other._id


@dataclasses.dataclass(frozen=True)
class RestrictedUniqueIdentifier(UniqueString):
    string: String
    # pattern = re.compile(r"^[a-zA-Z0-9_+\-.]+$")


class UniqueTag(UniqueString):
    category = "tag"


class UniqueScoreboardObjective(UniqueString):
    category = "scoreboard_objective"


class UniqueScoreboardPlayer(UniqueString):
    category = "scoreboard_player"


@dataclasses.dataclass(frozen=True)
class Comment(String):
    comment: str

    def get_str(
        self,
        existing_strings: dict[str, set[str]],
        resolve_string: typing.Callable[[String], str]
    ) -> tuple[str, str]:
        return f"# {self.comment}", "comment"
