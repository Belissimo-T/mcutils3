from __future__ import annotations

import abc
import ast
import dataclasses
import typing

from . import blocks, tree
from .. import strings, stores
from ..errors import CompilationError, compile_assert


@dataclasses.dataclass
class Scope:
    symbols: dict[str, stores.ReadableStore | typing.Callable[[ast.expr], McFunction]] = dataclasses.field(
        default_factory=dict)
    parent: Scope | None = None

    def get(self, name: str):
        try:
            return self.symbols[name]
        except KeyError:
            if self.parent is None:
                raise CompilationError(f"Variable {name!r} is not defined.")
            else:
                return self.parent.get(name)

    @classmethod
    def from_function2(cls, func: blocks.Function2) -> Scope:
        var_types: dict[str, tree.VariableType] = func.args

        for block in func.blocks.values():
            for statement in block.statements:
                if isinstance(statement, tree.AssignmentStatement):
                    if statement.target_type is not None:
                        if statement.target_type != var_types.get(statement.target, None) is not None:
                            raise CompilationError(
                                f"Variable {statement.target!r} has type {var_types[statement.target]} but is assigned "
                                f"to {statement.target_type}."
                            )
                        var_types[statement.target] = statement.target_type

        scope = cls()

        for name, var_type in var_types.items():
            if isinstance(var_type, tree.ScoreType):
                scope.symbols[name] = stores.ScoreboardStore(
                    strings.UniqueScoreboardPlayer(strings.LiteralString(name)), "__mcutils3__")
            elif isinstance(var_type, tree.NbtType):
                compile_assert(False)
                # scope.symbols[name] = stores.NbtStore(var_type.dtype)
            elif isinstance(var_type, tree.LocalScopeType):
                compile_assert(False)
                # scope.symbols[name] = stores.LocalScopeStore(var_type.dtype)
            else:
                raise CompilationError(f"Invalid variable type {var_type!r}.")

        return scope


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

    @classmethod
    def from_function2(cls, func: blocks.Function2) -> Function3:
        mcfunctions = {}
        scope = Scope.from_function2(func)

        for path, block in func.blocks.items():
            mcfunctions[path] = McFunction.from_block(block, scope)

        return cls(mcfunctions, func.args, func.entry_point)


@dataclasses.dataclass
class LocationOfString(strings.String):
    mcfunction: McFunction

    def get_str(self, existing_strings: set[str], resolve_string: typing.Callable[[strings.String], str]) -> str:
        return "current-location-string-todo"  # TODO


@dataclasses.dataclass
class McFunction:
    commands: list[strings.String]

    @classmethod
    def from_block(cls, block: blocks.Block, scope: Scope):
        commands = []

        for statement in block.statements:
            match statement:
                case tree.AssignmentStatement(target=target, value=value):
                    target = scope.get(target)
                    breakpoint()
                case tree.ExpressionStatement(expression=expression):
                    breakpoint()
                case blocks.IfStatement(condition=condition, true_block=true_block, false_block=false_block):
                    breakpoint()
                case blocks.BlockCallStatement(mcfunction=mcfunction):
                    commands.append(
                        strings.LiteralString("function %s", LocationOfString())
                    )

        return cls(commands)
