from __future__ import annotations

import ast
import dataclasses
import typing

import mcutils.ir.tree
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
    def from_namespace2(cls, namespace: blocks.Namespace2, std_lib_config: StdLibConfig | None) -> Namespace3:
        functions = {}

        for path, func in namespace.functions.items():
            functions[path] = Function3()

        for path, func in namespace.functions.items():
            functions[path].preprocess(func)

        for path, func in namespace.functions.items():
            functions[path].process(func, functions, std_lib_config)

        return cls(functions)


@dataclasses.dataclass
class StdLibConfig:
    stack_push: tuple[str, ...]
    stack_pop: tuple[str, ...]
    stack_peek: tuple[str, ...]


class Function3:
    mcfunctions: dict[tuple[str, ...], McFunction]
    args: dict[str, tree.VariableType]
    entry_point: tuple[str, ...] = ()
    symbols: dict[str, stores.WritableStore | stores.ReadableStore] = dataclasses.field(default_factory=dict)

    def process(self, func: blocks.BlockedFunction, functions: dict[tuple[str, ...], Function3],
                std_lib_config: StdLibConfig | None) -> Function3:
        for path, block in func.blocks.items():
            commands = []

            for statement in block.statements:
                # transform stack operations to function calls
                match statement:
                    case blocks_expr.StackPushStatement(value=value):
                        compile_assert(std_lib_config is not None, "std lib is required for stack operations")

                        std_stack_push_func = functions[std_lib_config.stack_push]
                        std_arg = std_stack_push_func.symbols["STD_ARG"]

                        commands += [
                            *stores_conv.var_to_var(value, std_arg),
                            strings.LiteralString(
                                "function %s",
                                LocationOfString(std_stack_push_func.mcfunctions[std_stack_push_func.entry_point])
                            )
                        ]
                    case blocks_expr.StackPopStatement(dst=dst):
                        compile_assert(std_lib_config is not None, "std lib is required for stack operations")

                        std_stack_pop_func = functions[std_lib_config.stack_pop]
                        std_ret = std_stack_pop_func.symbols["STD_RET"]

                        commands += [
                            strings.LiteralString(
                                "function %s",
                                LocationOfString(std_stack_pop_func.mcfunctions[std_stack_pop_func.entry_point])
                            ),
                            *stores_conv.var_to_var(std_ret, dst),
                        ]

                    # match statement:
                    case blocks_expr.ConditionalBlockCallStatement(condition=condition, true_block=true_block,
                                                                   unless=unless):
                        mcfunction = self.mcfunctions[true_block]
                        commands.append(
                            strings.LiteralString(
                                f"execute {'if' if unless else 'unless'} score %s %s matches 0 run function %s",
                                *condition, LocationOfString(mcfunction))
                        )
                        pass
                    case blocks.BlockCallStatement(block=mcfunction_path):
                        mcfunction = self.mcfunctions[mcfunction_path]
                        commands.append(
                            strings.LiteralString("function %s", LocationOfString(mcfunction))
                        )
                    case blocks.FunctionCallStatement(function=function):
                        func = functions[function]
                        mcfunction = func.mcfunctions[func.entry_point]
                        commands.append(
                            strings.LiteralString("function %s", LocationOfString(mcfunction))
                        )
                    case tree.LiteralStatement(strings=strings_):
                        commands += strings_
                    case blocks_expr.InPlaceOperationStatement(src=src, dst=dst, op=op):
                        commands += stores_conv.op_in_place(
                            dst=dst, src=src, op=op
                        )


                    case tree.CommentStatement(message=msg):
                        commands.append(strings.Comment(msg))
                    case _:
                        breakpoint()

            self.mcfunctions[path].commands = commands

        ...

    def preprocess(self, func: blocks.BlockedFunction):
        mcfunctions = {path: McFunction([]) for path in func.blocks}

        self.mcfunctions = mcfunctions
        self.args = func.args
        self.entry_point = func.entry_point
        self.symbols = func.symbols


@dataclasses.dataclass
class LocationOfString(strings.String):
    mcfunction: McFunction

    def get_str(
        self,
        existing_strings: dict[str, set[str]],
        resolve_string: typing.Callable[[strings.String], str]
    ) -> tuple[str, str]:
        compile_assert(self.mcfunction.location is not None)
        return self.mcfunction.location.to_str(), "location"

    def __hash__(self):
        return hash(id(self))

    def __eq__(self, other):
        return id(self) == id(other)


@dataclasses.dataclass
class McFunction:
    commands: list[strings.String]
    location: Location | None = None
