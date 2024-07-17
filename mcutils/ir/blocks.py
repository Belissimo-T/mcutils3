from __future__ import annotations

import ast
import dataclasses
import typing

from . import tree, compile_control_flow
from ..data import stores, expressions, object_model
from ..errors import compile_assert
from ..ir import tree_statements_base

_IF_TEMP = object_model.get_temp_var("conditional")


@dataclasses.dataclass
class BlockedFunction:
    blocks: dict[tuple[str, ...], Block]
    args: tuple[str, ...]
    entry_point: tuple[str, ...] = ()
    symbols: dict[str, stores.ReadableStore | stores.WritableStore] = dataclasses.field(default_factory=dict)

    @staticmethod
    def _find_free(container, base: tuple[str, ...], name: str):
        i = 2
        new_name = name
        while base + (new_name,) in container:
            new_name = f"{name}{i}"
            i += 1

        return base + (new_name,)

    @classmethod
    def process_block(
        cls,
        statements: list[tree_statements_base.Statement],
        continuation_info: ContinuationInfo,
        blocks: dict[tuple[str, ...], Block],
        path: tuple[str, ...] = ()
    ):
        b = Block([], continuation_info.with_())
        blocks[path] = b

        for statement in statements:
            if isinstance(statement, tree.IfStatement):
                stmt = IfStatement(
                    condition=statement.condition,
                    true_block=cls._find_free(blocks, path, "__if_true"),
                    false_block=cls._find_free(blocks, path, "__if_false")
                )

                b.statements.append(stmt)
                cls.process_block(statements=statement.true_body, continuation_info=continuation_info,
                                  path=stmt.true_block, blocks=blocks)
                cls.process_block(statements=statement.false_body, continuation_info=continuation_info,
                                  path=stmt.false_block, blocks=blocks)

            elif isinstance(statement, tree.WhileLoopStatement):
                while_path = cls._find_free(blocks, path, "__while")

                stmt = WhileStatement(
                    condition=statement.condition,
                    body=while_path
                )

                b.statements.append(stmt)
                cls.process_block(
                    statements=statement.body,
                    continuation_info=continuation_info,
                    path=stmt.body,
                    blocks=blocks
                )
            else:
                compile_assert(not isinstance(statement, tree.NestedStatement))
                b.statements.append(statement)

    @classmethod
    def from_tree_function(cls, func: tree.TreeFunction, std_lib_config: StdLibConfig) -> BlockedFunction:
        out = cls(
            blocks={("__return",): Block([], ContinuationInfo(return_=None))},
            args=func.args,
            entry_point=(),
            symbols=func.scope.collapse().variables
        )
        cls.process_block(statements=func.statements, blocks=out.blocks,
                          continuation_info=ContinuationInfo(return_=("__return",)))

        out.blocks = compile_control_flow.transform_all(out.blocks)

        for block_path in list(out.blocks.keys()):
            block = out.blocks[block_path]
            new_statements = []

            for statement in block.statements:
                match statement:
                    case IfStatement(condition=condition, true_block=true_block, false_block=false_block):
                        if_reset_cond_var_path = cls._find_free(out.blocks, block_path, "__if_reset_cond_var")
                        # noinspection PyTypeChecker
                        if_reset_cond_var = Block(
                            statements=[
                                BlockCallStatement(true_block),
                                SimpleAssignmentStatement(
                                    src=stores.ConstInt(1),
                                    dst=_IF_TEMP
                                ),
                            ],

                            continuation_info=None
                        )

                        out.blocks[if_reset_cond_var_path] = if_reset_cond_var

                        new_statements += [
                            *expressions.fetch(condition, _IF_TEMP),
                            ConditionalBlockCallStatement(
                                condition=_IF_TEMP,
                                true_block=if_reset_cond_var_path,
                                unless=False
                            ),
                            ConditionalBlockCallStatement(
                                condition=_IF_TEMP,
                                true_block=false_block,
                                unless=True
                            )
                        ]
                    case _:
                        new_statements.append(statement)

            block.statements = new_statements

        for block in out.blocks.values():
            new_statements = cls.transform_returns(block.statements)
            new_statements = cls.transform_assignments(new_statements)
            new_statements = cls.transform_stack_ops(new_statements, std_lib_config)
            new_statements = cls.transform_assignments(new_statements)
            new_statements = cls.transform_stack_ops(new_statements, std_lib_config)
            new_statements = cls.transform_assignments(new_statements)

            new2_statements = []
            for statement in new_statements:
                match statement:
                    case FunctionCallStatement(
                        function=function,
                        compile_time_args=compile_time_args
                    ) if len(function) == 1 and func.scope.contains(function[0], "pyfunc"):
                        new2_statements += func.scope.get(function[0], "pyfunc")(*compile_time_args)
                    case _:
                        new2_statements.append(statement)

            block.statements = new2_statements

        used_blocks = out.get_used_blocks(out.entry_point)
        out.blocks = {k: v for k, v in out.blocks.items() if k in used_blocks}

        return out

    def _get_used_blocks(self, block: tuple[str, ...], out: set[tuple[str, ...]]):
        if block in out:
            return

        out.add(block)

        for call in self.blocks[block].get_calls():
            self._get_used_blocks(call, out)

    def get_used_blocks(self, block: tuple[str, ...]) -> set[tuple[str, ...]]:
        out = set()
        self._get_used_blocks(block, out)
        return out

    @staticmethod
    def transform_returns(
        statements: list[tree_statements_base.Statement]
    ) -> list[tree_statements_base.Statement]:
        out = []

        for statement in statements:
            match statement:
                case tree.ReturnStatement(value=value):
                    if value is not None:
                        out.append(tree.AssignmentStatement(value, object_model.RET_VALUE))
                case _:
                    out.append(statement)

        return out

    @staticmethod
    def transform_assignments(statements: list[tree_statements_base.Statement]) -> list[tree_statements_base.Statement]:
        out = []

        for statement in statements:
            match statement:
                case tree.AssignmentStatement(src=src, dst=dst):
                    out += expressions.fetch(src, dst)
                case _:
                    out.append(statement)

        return out

    @staticmethod
    def transform_stack_ops(
        statements: list[tree_statements_base.Statement],
        std_lib_config: StdLibConfig
    ) -> list[tree_statements_base.Statement]:
        out = []

        for statement in statements:
            match statement:
                case tree.StackPopStatement(dst=dst):
                    out.append(tree.AssignmentStatement(
                        expressions.FunctionCallExpression(
                            function=std_lib_config.stack_pop[0],
                            args=(),
                            compile_time_args=std_lib_config.stack_pop[1]
                        ),
                        dst
                    ))
                case tree.StackPushStatement(src=src):
                    out.append(tree.AssignmentStatement(
                        expressions.FunctionCallExpression(
                            function=std_lib_config.stack_push[0],
                            args=(src,),
                            compile_time_args=std_lib_config.stack_push[1]
                        ),
                        None
                    ))
                case _:
                    out.append(statement)

        return out


@dataclasses.dataclass(frozen=True)
class ContinuationInfo:
    return_: tuple[str, ...] | None
    default: tuple[str, ...] | None = None
    loops: list[LoopContinuationInfo] = dataclasses.field(default_factory=list)
    children: list[ContinuationInfo] = dataclasses.field(default_factory=list)

    def with_(self, default: tuple[str, ...] | None = None,
              new_loops: list[LoopContinuationInfo] = None) -> typing.Self:
        # noinspection PyArgumentList
        return self.__class__(
            default=self.default if default is None else default,
            return_=self.return_,
            loops=self.loops.copy() if new_loops is None else self.loops + new_loops
        )


@dataclasses.dataclass
class LoopContinuationInfo:
    continue_: tuple[str, ...]
    break_: tuple[str, ...]


@dataclasses.dataclass
class Block:
    statements: list[tree_statements_base.Statement]
    continuation_info: ContinuationInfo
    parent_block: tuple[str, ...] | None = None

    def get_calls(self) -> list[tuple[str, ...]]:
        out = []
        for statement in self.statements:
            match statement:
                case BlockCallStatement(block=block):
                    out.append(block)
                case ConditionalBlockCallStatement(true_block=true_block):
                    out.append(true_block)
                case _:
                    pass
        return out


@dataclasses.dataclass
class IfStatement(tree_statements_base.StoppingStatement):
    condition: stores.ReadableStore
    true_block: tuple[str, ...]
    false_block: tuple[str, ...]
    no_redirect_branches: bool = False


@dataclasses.dataclass
class WhileStatement(tree_statements_base.Statement):
    condition: stores.ReadableStore
    body: tuple[str, ...]


@dataclasses.dataclass
class BlockCallStatement(tree_statements_base.StoppingStatement):
    block: tuple[str, ...]


@dataclasses.dataclass
class FunctionCallStatement(tree_statements_base.Statement):
    function: tuple[str, ...]
    compile_time_args: tuple[ast.Constant | ast.Name, ...]


@dataclasses.dataclass
class ConditionalBlockCallStatement(tree_statements_base.Statement):
    condition: stores.ScoreboardStore
    true_block: tuple[str, ...]
    unless: bool = False


@dataclasses.dataclass
class SimpleAssignmentStatement(tree_statements_base.Statement):
    src: stores.PrimitiveReadableStore
    dst: stores.PrimitiveWritableStore


@dataclasses.dataclass
class StdLibConfig:
    stack_push: tuple[tuple[str, ...], tuple]
    stack_pop: tuple[tuple[str, ...], tuple]
    stack_peek: tuple[tuple[str, ...], tuple]
