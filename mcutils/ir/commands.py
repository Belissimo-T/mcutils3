from __future__ import annotations

import ast
import dataclasses
import typing

import mcutils.ir.tree
from . import blocks, tree, blocks_expr
from .. import strings
from ..data import stores, stores_conv, expressions
from ..errors import CompilationError, compile_assert
from ..lib import std, tools
from ..location import Location


@dataclasses.dataclass
class Namespace3:
    functions: dict[tuple[str, ...], Function3]

    @classmethod
    def from_namespace2(cls, namespace: blocks.Namespace2) -> Namespace3:
        functions = {}

        for path, func in namespace.functions.items():
            functions[path] = Function3()

        for path, func in namespace.functions.items():
            functions[path].process(func, functions)

        return cls(functions)


class Function3:
    mcfunctions: dict[tuple[str, ...], McFunction]
    args: dict[str, tree.VariableType]
    entry_point: tuple[str, ...] = ()
    symbols: dict[str, stores.ReadableStore] = dataclasses.field(default_factory=dict)

    def process(self, func: blocks.Function2, functions: dict[tuple[str, ...], Function3]) -> Function3:
        from ..lib import stack
        mcfunctions = {path: McFunction([]) for path in func.blocks}

        for path, block in func.blocks.items():
            commands = []

            for statement in block.statements:
                # transform stack operations to function calls
                match statement:
                    case blocks_expr.StackPushStatement(value=value):
                        commands += [
                            *stores_conv.var_to_var(value, std.STD_ARG),
                            *stack.std_stack_push(0)
                        ]
                    case blocks_expr.StackPopStatement(dst=dst):
                        commands += [
                            *stack.std_stack_pop(0),
                            *stores_conv.var_to_var(std.STD_RET, dst),
                        ]

                match statement:
                    case blocks_expr.ConditionalBlockCallStatement(condition=condition, true_block=true_block,
                                                                   unless=unless):
                        mcfunction = mcfunctions[true_block]
                        commands.append(
                            strings.LiteralString(
                                f"execute {'if' if unless else 'unless'} score %s %s matches 0 run function %s",
                                *condition, LocationOfString(mcfunction))
                        )
                        pass
                    case blocks.BlockCallStatement(block=mcfunction_path):
                        mcfunction = mcfunctions[mcfunction_path]
                        commands.append(
                            strings.LiteralString("function %s", LocationOfString(mcfunction))
                        )
                    case blocks.FunctionCallStatement(function=function, compile_time_args=compile_time_args):
                        if function == ("print", ):
                            # TODO
                            commands += []
                        else:
                            func = functions[function]
                            mcfunction = func.mcfunctions[func.entry_point]
                            commands.append(
                                strings.LiteralString("function %s", LocationOfString(mcfunction))
                            )
                    case mcutils.ir.tree.LiteralStatement(strings=strings_):
                        commands += strings_
                    case blocks_expr.ReturnStatement(value=value):
                        commands += stores_conv.var_to_var(value, std.STD_RET)
                    case _:
                        breakpoint()

            mcfunctions[path].commands = commands

        self.mcfunctions = mcfunctions
        self.args = func.args
        self.entry_point = func.entry_point
        self.symbols = func.symbols


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
