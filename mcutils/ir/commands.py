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
class CompileNamespace:
    function_templates: dict[tuple[str, ...], tree.FunctionTemplate]
    scope: tree.Scope
    tree_functions: dict[tuple[str, ...], tree.Function] = dataclasses.field(default_factory=dict)
    blocked_functions: dict[tuple[str, ...], blocks.BlockedFunction] = dataclasses.field(default_factory=dict)
    command_functions: dict[tuple[str, ...], CommandFunction] = dataclasses.field(default_factory=dict)

    @classmethod
    def from_tree_namespace(cls, namespace: tree.File) -> CompileNamespace:
        return cls(
            function_templates=namespace.function_templates,
            scope=namespace.scope
        )

    def resolve_templates(self, start: list[str], std_lib_config: StdLibConfig | None = None):
        stack: list[tuple[tuple[str, ...], tuple]] = [((name,), ()) for name in start]
        processed_command_functions: set[tuple[str, ...]] = set()

        iterations_with_no_change = 0
        while stack:
            changed = False
            for i, (func_name, args) in enumerate(stack):
                print(f"=> Attempting compile if {func_name} with {args=}.")
                try:
                    func_template = self.function_templates[func_name]
                except KeyError:
                    raise CompilationError(f"Undefined function {func_name!r}")

                func_path = (*func_name, tree.compile_time_args_to_str(args))

                if func_path in processed_command_functions:
                    print(" -> Already processed.")
                    stack.pop(i)
                    break

                ctime_arg_names = func_template.get_compile_time_args()
                compile_assert(len(ctime_arg_names) == len(args), "Missing compile time args.")

                scope = tree.Scope(
                    parent_scope=self.scope,
                    compile_time_args=dict(zip(ctime_arg_names, args)),
                    compile_function_template=lambda x, y: stack.append((x, y))
                )

                if func_path not in self.command_functions:
                    self.tree_functions[func_path] = tree.Function.from_py_ast(
                        func_template.node, scope
                    )

                    self.blocked_functions[func_path] = blocks.BlockedFunction.from_tree_function(
                        self.tree_functions[func_path], scope
                    )

                    self.command_functions[func_path] = CommandFunction()
                    self.command_functions[func_path].preprocess(self.blocked_functions[func_path])

                    # print(f" -> Got {len(dependencies)} dependencies.")

                    dependencies = self.command_functions[func_path].get_dependencies(self.blocked_functions[func_path], scope)

                    for (template_path, compile_time_args) in dependencies:
                        # dep_func_path = (*template_path, tree.compile_time_args_to_str(compile_time_args))
                        # if ((template_path, compile_time_args) not in stack) and (dep_func_path not in self.command_functions):
                        #     breakpoint()
                        # breakpoint()
                        stack.append((template_path, compile_time_args))
                else:
                    dependencies = self.command_functions[func_path].get_dependencies(self.blocked_functions[func_path],
                                                                                      scope)
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
                        std_lib_config=std_lib_config
                    )
                    stack.pop(i)
                    processed_command_functions.add(func_path)
                    # breakpoint()
                    print(f" -> Done! {func_path} with {dependencies}.")
                    changed = True
                    break

                print(" -> Waiting for dependencies.")


            if changed:
                iterations_with_no_change = 0

            else:
                iterations_with_no_change += 1
                if iterations_with_no_change > 5:
                    raise CompilationError("Circular dependency detected... Or something like that.")



@dataclasses.dataclass
class StdLibConfig:
    stack_push: tuple[str, ...]
    stack_pop: tuple[str, ...]
    stack_peek: tuple[str, ...]


class CommandFunction:
    mcfunctions: dict[tuple[str, ...], McFunction]
    args: dict[str, tree.VariableType]
    entry_point: tuple[str, ...] = ()
    symbols: dict[str, stores.WritableStore | stores.ReadableStore] = dataclasses.field(default_factory=dict)

    def process(
        self,
        func: blocks.BlockedFunction,
        functions: dict[tuple[str, ...], CommandFunction],
        scope: tree.Scope,
        std_lib_config: StdLibConfig | None
    ):
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
                    case blocks.FunctionCallStatement(function=function, compile_time_args=_compile_time_args):
                        compile_time_args = []
                        for el in _compile_time_args:
                            match el:
                                case ast.Constant(value=value):
                                    compile_time_args.append(value)
                                case ast.Name(id=id):
                                    try:
                                        compile_time_args.append(scope.get(id, ("string", "pyfunc", "compile_time_arg")))
                                    except LookupError:
                                        compile_time_args.append(self.symbols[id])

                        func_path = (*function, tree.compile_time_args_to_str(tuple(compile_time_args)))
                        func = functions[func_path]
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

    def preprocess(self, func: blocks.BlockedFunction) -> list[tuple[str, ...], tuple]:
        mcfunctions = {path: McFunction([]) for path in func.blocks}

        self.mcfunctions = mcfunctions
        self.args = func.args
        self.entry_point = func.entry_point
        self.symbols = func.symbols

    def get_dependencies(self, func: blocks.BlockedFunction, scope: tree.Scope):
        deps = []
        for path, block in func.blocks.items():
            for statement in block.statements:
                match statement:
                    case blocks.FunctionCallStatement(function=function, compile_time_args=_compile_time_args):
                        compile_time_args = []
                        for el in _compile_time_args:
                            match el:
                                case ast.Constant(value=value):
                                    compile_time_args.append(value)
                                case ast.Name(id=id):
                                    try:
                                        compile_time_args.append(scope.get(id, ("string", "pyfunc", "compile_time_arg")))
                                    except LookupError:
                                        compile_time_args.append(self.symbols[id])
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
