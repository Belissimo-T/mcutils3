from __future__ import annotations

import abc
import dataclasses
import itertools
import typing

from .errors import CompilationError


class IdentifierResolver:
    def __init__(self):
        self.identifiers: dict[Identifier, str] = {}
        self.strings: set[str] = set()

    def resolve_identifier(self, identifier: Identifier) -> str:
        if identifier in self.identifiers:
            return self.identifiers[identifier]
        else:
            val = identifier.get_str(self.strings, self.resolve_identifier)
            self.identifiers[identifier] = val
            self.strings.add(val)
            return val


@dataclasses.dataclass(frozen=True)
class Identifier(abc.ABC):
    @abc.abstractmethod
    def get_str(self, existing_identifiers: set[str], resolve_identifier: typing.Callable[[Identifier], str]) -> str:
        ...


@dataclasses.dataclass(frozen=True)
class LiteralIdentifier(Identifier):
    literal: str
    args: tuple[Identifier, ...] = ()

    def get_str(self, existing_identifiers: set[str], resolve_identifier: typing.Callable[[Identifier], str]) -> str:
        format_args = tuple(map(resolve_identifier, self.args))

        try:
            return self.literal % format_args
        except TypeError as e:
            raise CompilationError(f"Command {self.literal!r} has {len(self.args)} args.") from e


class CurrentLocationIdentifier(Identifier):
    def get_str(self, existing_identifiers: set[str], resolve_identifier: typing.Callable[[Identifier], str]) -> str:
        return "current-location-string-todo"  # TODO


@dataclasses.dataclass(frozen=True)
class UniqueIdentifier(Identifier, abc.ABC):
    string: Identifier

    counter: typing.Iterable[typing.Callable[[str], str]] = dataclasses.field(
        default_factory=lambda: ((lambda x, __n=n: x + __n) for n in map(str, itertools.count(2))))

    def get_str(self, existing_identifiers: set[str], resolve_identifier: typing.Callable[[Identifier], str]) -> str:
        val = resolve_identifier(self.string)

        for counter in itertools.chain([lambda x: x], self.counter):
            new_val = counter(val)

            if new_val not in existing_identifiers:
                return new_val


class RestrictedUniqueIdentifier(UniqueIdentifier):
    string = LiteralIdentifier("%s", (CurrentLocationIdentifier(),))
    # pattern = re.compile(r"^[a-zA-Z0-9_+\-.]+$")


class UniqueTag(UniqueIdentifier): pass


class UniqueScoreboardObjective(UniqueIdentifier): pass


class UniqueScoreboardPlayer(UniqueIdentifier): pass
