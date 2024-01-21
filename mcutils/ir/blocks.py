from __future__ import annotations

import dataclasses
import typing

from . import tree


@dataclasses.dataclass
class Namespace2:
    functions: dict[tuple[str, ...], Function2]

    @classmethod
    def from_tree_namespace(cls, namespace: tree.Namespace) -> Namespace2:
        return cls({
            name: Function2.from_tree_function(func)
            for name, func in namespace.symbols.items()
        })


@dataclasses.dataclass
class Function2:
    blocks: dict[tuple[str, ...], Block]
    args: dict[str, tree.VariableType]
    entry_point: tuple[str, ...] = ()

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
                b.statements.append(statement)

    @classmethod
    def from_tree_function(cls, func: tree.Function) -> Function2:
        out = cls(
            {("__return",): Block([], ContinuationInfo(return_=None))},
            func.args
        )
        cls.process_block(statements=func.statements, blocks=out.blocks,
                          continuation_info=ContinuationInfo(return_=("__return",)))
        return out


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


@dataclasses.dataclass
class WhileStatement(tree.Statement):
    condition: tree.Expression
    body: tuple[str, ...]


@dataclasses.dataclass
class BlockCallStatement(tree.StoppingStatement):
    block: tuple[str, ...]
