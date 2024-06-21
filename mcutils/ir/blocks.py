from __future__ import annotations

import ast
import dataclasses
import typing

from . import tree, blocks_expr, compile_control_flow
from .. import strings
from ..data import stores, expressions
from ..errors import CompilationError, compile_assert
from ..lib import std




_IF_TEMP = std.get_temp_var("conditional")


@dataclasses.dataclass
class BlockedFunction:
    blocks: dict[tuple[str, ...], Block]
    args: dict[str, tree.VariableType]
    entry_point: tuple[str, ...] = ()
    symbols: dict[str, stores.ReadableStore] = dataclasses.field(default_factory=dict)

    @staticmethod
    def _find_free(container, base: tuple[str, ...], name: str):
        i = 2
        new_name = name
        while base + (new_name,) in container:
            new_name = f"{name}{i}"

        return base + (new_name,)

    @classmethod
    def process_block(cls, statements: list[tree.Statement], continuation_info: ContinuationInfo,
                      blocks: dict[tuple[str, ...], Block],
                      path: tuple[str, ...] = ()):
        b = Block([], continuation_info)
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
                cls.process_block(statements=statement.body, continuation_info=continuation_info, path=stmt.body,
                                  blocks=blocks)
            else:
                compile_assert(not isinstance(statement, tree.NestedStatement))
                b.statements.append(statement)

    @classmethod
    def from_tree_function(cls, func: tree.Function, scope: tree.Scope) -> BlockedFunction:
        out = cls(
            blocks={("__return",): Block([], ContinuationInfo(return_=None))},
            args=func.args,
            entry_point=(),
            symbols={}
        )
        cls.process_block(statements=func.statements, blocks=out.blocks,
                          continuation_info=ContinuationInfo(return_=("__return",)))

        out.symbols = cls.get_symbols(out.blocks.values(), scope.variables | func.scope.collapse().variables | out.args)

        out.blocks = compile_control_flow.transform_all(out.blocks)

        for block in out.blocks.values():
            block.statements = blocks_expr.transform_exprs_in_stmts(block.statements, out.symbols)

        for block in out.blocks.values():
            new_statements = []
            for statement in block.statements:
                match statement:
                    case blocks_expr.AssignmentStatement(src=src, dst=dst):
                        new_statements += expressions.fetch(src, dst)
                    case blocks_expr.ExpressionStatement(expression=expression):
                        new_statements += expressions.fetch(expression, stores.NbtStore("storage", "mcutils", "null"))
                    case blocks_expr.IfStatement(condition=condition, true_block=true_block, false_block=false_block):
                        # breakpoint()
                        new_statements += [
                            *expressions.fetch(condition, _IF_TEMP),
                            blocks_expr.StackPushStatement(_IF_TEMP),
                            blocks_expr.ConditionalBlockCallStatement(
                                condition=_IF_TEMP,
                                true_block=true_block,
                                unless=False
                            ),
                            blocks_expr.StackPopStatement(_IF_TEMP),
                            blocks_expr.ConditionalBlockCallStatement(
                                condition=_IF_TEMP,
                                true_block=false_block,
                                unless=True
                            )
                        ]
                    case _:
                        new_statements.append(statement)

            block.statements = new_statements

        return out

    @staticmethod
    def get_symbols(blocks: typing.Iterable[Block], args: dict[str, tree.VariableType]):
        var_types: dict[str, tree.VariableType] = args.copy()

        # for block in blocks:
        #     for statement in block.statements:
        #         if isinstance(statement, tree.AssignmentStatement):
        #             if statement.target_type is not None:
        #                 if statement.target_type != var_types.get(statement.target, None) is not None:
        #                     raise CompilationError(
        #                         f"Variable {statement.target!r} has type {var_types[statement.target]} but is assigned "
        #                         f"to {statement.target_type}."
        #                     )
        #                 var_types[statement.target] = statement.target_type

        symbols = {}

        for name, var_type in var_types.items():
            match var_type:
                case tree.ScoreType(player=None, objective=None):
                    symbols[name] = std.get_temp_var("__user_" + name)
                case tree.ScoreType(player=None, objective=obj):
                    symbols[name] = stores.ScoreboardStore(strings.UniqueScoreboardPlayer("__user_" + name), obj)
                case tree.ScoreType(player=player, objective=None):
                    symbols[name] = stores.ScoreboardStore(player, std.MCUTILS_STD_OBJECTIVE)
                case tree.ScoreType(player=player, objective=obj):
                    symbols[name] = stores.ScoreboardStore(player, obj)
                case tree.NbtType():
                    compile_assert(False)
                    # scope.symbols[name] = stores.NbtStore(var_type.dtype)
                case tree.LocalScopeType():
                    compile_assert(False)
                    # scope.symbols[name] = stores.LocalScopeStore(var_type.dtype)
                case _:
                    raise CompilationError(f"Invalid variable type {var_type!r}.")

        return symbols


@dataclasses.dataclass
class ContinuationInfo:
    return_: tuple[str, ...] | None
    default: tuple[str, ...] | None = None
    loops: list[LoopContinuationInfo] = dataclasses.field(default_factory=list)

    def with_(self, default: tuple[str, ...] | None = None,
              new_loops: list[LoopContinuationInfo] = None) -> typing.Self:
        # noinspection PyArgumentList
        return self.__class__(
            default=self.default if default is None else default,
            return_=self.return_,
            loops=self.loops if new_loops is None else self.loops + new_loops
        )


@dataclasses.dataclass
class LoopContinuationInfo:
    continue_: tuple[str, ...]
    break_: tuple[str, ...]


@dataclasses.dataclass
class Block:
    statements: list[tree.Statement]
    continuation_info: ContinuationInfo


@dataclasses.dataclass
class IfStatement(tree.StoppingStatement):
    condition: tree.Expression
    true_block: tuple[str, ...]
    false_block: tuple[str, ...]
    no_redirect_branches: bool = False


@dataclasses.dataclass
class WhileStatement(tree.Statement):
    condition: tree.Expression
    body: tuple[str, ...]


@dataclasses.dataclass
class BlockCallStatement(tree.StoppingStatement):
    block: tuple[str, ...]


@dataclasses.dataclass
class FunctionCallStatement(tree.Statement):
    function: tuple[str, ...]
    compile_time_args: tuple[ast.Constant | ast.Name, ...]
