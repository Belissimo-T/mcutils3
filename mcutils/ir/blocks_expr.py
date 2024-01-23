import dataclasses

from . import blocks
from ..data import stores, expressions
from ..errors import compile_assert
from ..ir import tree


@dataclasses.dataclass
class ExpressionStatement(tree.Statement):
    expression: stores.ReadableStore


@dataclasses.dataclass
class IfStatement(tree.StoppingStatement):
    condition: stores.ReadableStore
    true_block: tuple[str, ...]
    false_block: tuple[str, ...]


@dataclasses.dataclass
class AssignmentStatement(tree.Statement):
    src: stores.ReadableStore
    dst: stores.WritableStore


@dataclasses.dataclass
class ReturnStatement(tree.StoppingStatement):
    value: stores.ReadableStore


@dataclasses.dataclass
class StackPushStatement(tree.Statement):
    value: stores.ReadableStore


@dataclasses.dataclass
class StackPopStatement(tree.Statement):
    dst: stores.WritableStore


def transform_expr(expr: tree.Expression,
                   symbols: dict[str, stores.ReadableStore | stores.WritableStore]) -> stores.ReadableStore:
    match expr:
        case tree.SymbolExpression(name):
            return symbols[name]
        case tree.ConstantExpression(value):
            return stores.ConstStore(value)
        case tree.FunctionCallExpression(function=function, args=args, compile_time_args=compile_time_args):
            return expressions.FunctionCallExpression(
                function=function,
                args=tuple(transform_expr(arg, symbols) for arg in args),
                compile_time_args=compile_time_args
            )
        case tree.BinOpExpression(left=left, right=right, op=op):
            return expressions.BinOpExpression(
                left=transform_expr(left, symbols),
                right=transform_expr(right, symbols),
                op=op
            )
        case _:
            compile_assert(False)


def transform_exprs_in_stmts(stmts: list[tree.Statement],
                             symbols: dict[str, stores.ReadableStore | stores.WritableStore]
                             ) -> list[tree.Statement]:
    out = []
    for stmt in stmts:
        match stmt:
            case tree.ExpressionStatement(expression):
                out.append(ExpressionStatement(transform_expr(expression, symbols)))
            case tree.AssignmentStatement(target=target, value=value):
                out.append(AssignmentStatement(
                    src=transform_expr(value, symbols),
                    dst=symbols[target]
                ))
            case blocks.IfStatement(condition=condition, true_block=true_block, false_block=false_block):
                out.append(IfStatement(
                    condition=transform_expr(condition, symbols),
                    true_block=true_block,
                    false_block=false_block
                ))
            case tree.ReturnStatement(value=value):
                out.append(ReturnStatement(
                    value=transform_expr(value, symbols)
                ))
            case _:
                out.append(stmt)

    return out
