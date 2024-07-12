from __future__ import annotations

import dataclasses
import typing

from . import blocks
from .. import strings
from ..ir import tree
from ..data import stores, stores_conv
from ..errors import CompilationError, compile_assert
from ..location import Location


@dataclasses.dataclass
class CompileNamespace:
    function_templates: dict[tuple[str, ...], tree.FunctionTemplate]
    scope: tree.Scope
    tree_functions: dict[tuple[str, ...], tree.TreeFunction] = dataclasses.field(default_factory=dict)
    blocked_functions: dict[tuple[str, ...], blocks.BlockedFunction] = dataclasses.field(default_factory=dict)
    command_functions: dict[tuple[str, ...], CommandFunction] = dataclasses.field(default_factory=dict)

    @classmethod
    def from_tree_namespace(cls, namespace: tree.File) -> CompileNamespace:
        return cls(
            function_templates=namespace.function_templates,
            scope=namespace.scope
        )

    def resolve_templates(self, start: list[str], std_lib_config: blocks.StdLibConfig | None = None):
        stack: list[tuple[tuple[str, ...], tuple]] = (
            [std_lib_config.stack_peek, std_lib_config.stack_pop, std_lib_config.stack_push]
            + [((name,), ()) for name in start]
        )
        processed_command_functions: set[tuple[str, ...]] = set()

        iterations_with_no_change = 0
        while stack:
            changed = False
            for i, (func_name, args) in enumerate(stack):
                print(f"=> Attempting to compile {func_name} with {args=}.")
                try:
                    func_template = self.function_templates[func_name]
                except KeyError:
                    raise CompilationError(f"Undefined function {func_name!r}")

                func_path = (*func_name, tree.compile_time_args_to_str(args))

                if func_path in processed_command_functions:
                    print(" -> Already processed.")
                    stack.pop(i)
                    changed = True
                    break

                ctime_arg_names = func_template.get_compile_time_args()
                compile_assert(len(ctime_arg_names) == len(args), "Missing compile time args.")

                scope = tree.Scope(
                    parent_scope=self.scope,
                    compile_time_args=dict(zip(ctime_arg_names, args))
                )

                if func_path not in self.command_functions:
                    self.tree_functions[func_path] = tree.TreeFunction.from_py_ast(
                        func_template.node, scope
                    )

                    self.blocked_functions[func_path] = blocks.BlockedFunction.from_tree_function(
                        func=self.tree_functions[func_path],
                        std_lib_config=std_lib_config
                    )

                    self.command_functions[func_path] = CommandFunction()
                    self.command_functions[func_path].preprocess(self.blocked_functions[func_path])

                    # print(f" -> Got {len(dependencies)} dependencies.")

                    dependencies = self.command_functions[func_path].get_dependencies(self.blocked_functions[func_path])

                    for (template_path, compile_time_args) in dependencies:
                        stack.append((template_path, compile_time_args))
                else:
                    dependencies = self.command_functions[func_path].get_dependencies(self.blocked_functions[func_path])
                all_deps_compiled = True
                for template_path, compile_time_args in dependencies:
                    dep_func_path = (*template_path, tree.compile_time_args_to_str(compile_time_args))

                    if dep_func_path not in self.command_functions:
                        all_deps_compiled = False
                        break

                if all_deps_compiled:
                    self.command_functions[func_path].process(
                        func=self.blocked_functions[func_path],
                        functions=self.command_functions,
                        scope=scope,
                    )
                    stack.pop(i)
                    processed_command_functions.add(func_path)
                    # breakpoint()
                    print(f" -> Done! {func_path} with {dependencies}.")
                    changed = True
                    break
                else:
                    print(" -> Waiting for dependencies.")

            if changed:
                iterations_with_no_change = 0

            else:
                iterations_with_no_change += 1
                if iterations_with_no_change > 1:
                    raise CompilationError("Circular dependency detected... Or something like that.")


class CommandFunction:
    mcfunctions: dict[tuple[str, ...], McFunction]
    args: tuple[str, ...]
    entry_point: tuple[str, ...] = ()
    symbols: dict[str, stores.WritableStore | stores.ReadableStore] = dataclasses.field(default_factory=dict)

    def process(
        self,
        func: blocks.BlockedFunction,
        functions: dict[tuple[str, ...], CommandFunction],
        scope: tree.Scope,
    ):
        for path, block in func.blocks.items():
            commands = []

            for statement in block.statements:
                # transform stack operations to function calls
                match statement:
                    case blocks.ConditionalBlockCallStatement(condition=condition, true_block=true_block, unless=unless):
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
                    case blocks.FunctionCallStatement(function=function, compile_time_args=compile_time_args):
                        func_path = (*function, tree.compile_time_args_to_str(tuple(compile_time_args)))
                        func = functions[func_path]
                        mcfunction = func.mcfunctions[func.entry_point]
                        commands.append(
                            strings.LiteralString("function %s", LocationOfString(mcfunction))
                        )
                    case tree.LiteralStatement(strings=strings_):
                        commands += strings_
                    case tree.InPlaceOperationStatement(src=src, dst=dst, op=op):
                        commands += stores_conv.op_in_place(
                            dst=dst, src=src, op=op
                        )
                    case blocks.SimpleAssignmentStatement(src=src, dst=dst):
                        commands += stores_conv.var_to_var(src, dst)
                    case tree.CommentStatement(message=msg):
                        for line in msg.splitlines():
                            commands.append(strings.Comment(line))
                    case _:
                        breakpoint()

            self.mcfunctions[path].commands = commands

    def preprocess(self, func: blocks.BlockedFunction):
        mcfunctions = {path: McFunction([]) for path in func.blocks}

        self.mcfunctions = mcfunctions
        self.args = func.args
        self.entry_point = func.entry_point
        self.symbols = func.symbols

    @staticmethod
    def get_dependencies(func: blocks.BlockedFunction):
        deps = []
        for path, block in func.blocks.items():
            for statement in block.statements:
                match statement:
                    case blocks.FunctionCallStatement(function=function, compile_time_args=compile_time_args):
                        deps.append((function, tuple(compile_time_args)))

        return deps


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
