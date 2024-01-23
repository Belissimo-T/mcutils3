from __future__ import annotations

import ast
import dataclasses
import typing

from . import blocks, tree, blocks_expr
from .. import strings
from ..data import stores, stores_conv, expressions
from ..errors import CompilationError, compile_assert
from ..lib import std
from ..location import Location


@dataclasses.dataclass
class Namespace3:
    functions: dict[tuple[str, ...], Function3]

    @classmethod
    def from_namespace2(cls, namespace: blocks.Namespace2) -> Namespace3:
        functions = {}

        for path, func in namespace.functions.items():
            functions[path] = Function3.from_function2(func)

        return cls(functions)


@dataclasses.dataclass
class Function3:
    mcfunctions: dict[tuple[str, ...], McFunction]
    args: dict[str, tree.VariableType]
    entry_point: tuple[str, ...] = ()
    symbols: dict[str, stores.ReadableStore] = dataclasses.field(default_factory=dict)

    @classmethod
    def from_function2(cls, func: blocks.Function2) -> Function3:
        mcfunctions = {path: McFunction([]) for path in func.blocks}

        for path, block in func.blocks.items():
            commands = []

            for statement in block.statements:
                match statement:
                    case blocks_expr.AssignmentStatement(src=src, dst=dst):
                        # target = scope.get(target)
                        # breakpoint()
                        pass
                    case blocks_expr.ExpressionStatement(expression=expression):
                        # breakpoint()
                        pass
                    case blocks_expr.IfStatement(condition=condition, true_block=true_block, false_block=false_block):
                        # breakpoint()
                        pass
                    case blocks.BlockCallStatement(block=mcfunction_path):
                        mcfunction = mcfunctions[mcfunction_path]
                        commands.append(
                            strings.LiteralString("function %s", LocationOfString(mcfunction))
                        )
                    case tree.FunctionCallExpression():
                        breakpoint()
                    case _:
                        breakpoint()

            mcfunctions[path].commands = commands

        return cls(mcfunctions, func.args, func.entry_point, func.symbols)


@dataclasses.dataclass
class LocationOfString(strings.String):
    mcfunction: McFunction

    def get_str(self, existing_strings: set[str], resolve_string: typing.Callable[[strings.String], str]) -> str:
        compile_assert(self.mcfunction.location is not None)
        return self.mcfunction.location.to_str()

    def __hash__(self):
        return hash(id(self))

    def __eq__(self, other):
        return id(self) == id(other)


@dataclasses.dataclass
class McFunction:
    commands: list[strings.String]
    location: Location | None = None
