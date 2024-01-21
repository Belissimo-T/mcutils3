from __future__ import annotations

import ast
import dataclasses
import typing

from .. import stores
from ..errors import CompilationError, compile_assert


@dataclasses.dataclass
class Namespace:
    symbols: dict[tuple[str, ...], Function | stores.ReadableStore]

    @classmethod
    def from_py_ast(cls, node: ast.Module):
        functions = {}

        for stmt in node.body:
            if isinstance(stmt, ast.FunctionDef):
                functions[stmt.name,] = Function.from_py_ast(stmt)
            else:
                raise CompilationError(f"Invalid statement {stmt!r} in namespace {ast!r}")

        return cls(functions)


def statement_factory(node: ast.stmt) -> Statement:
    if isinstance(node, ast.Expr):
        return ExpressionStatement(expression_factory(node.value))
    elif isinstance(node, ast.While):
        return WhileLoopStatement(
            expression_factory(node.test),
            [statement_factory(stmt) for stmt in node.body]
        )
    elif isinstance(node, ast.If):
        return IfStatement.from_py_ast(node)
    elif isinstance(node, (ast.Assign, ast.AnnAssign)):
        return AssignmentStatement.from_py_ast(node)
    elif isinstance(node, ast.Return):
        return ReturnStatement(expression_factory(node.value))
    elif isinstance(node, ast.Continue):
        return ContinueStatement()
    elif isinstance(node, ast.Break):
        return BreakStatement()
    else:
        raise CompilationError(f"Invalid statement {node!r}")


def expression_factory(node: ast.expr) -> Expression:
    if isinstance(node, ast.UnaryOp):
        return UnaryOpExpression.from_py_ast(node)
    elif isinstance(node, (ast.Compare, ast.BinOp, ast.BoolOp)):
        return BinOpExpression.from_py_ast(node)
    elif isinstance(node, ast.Call):
        return FunctionCallExpression.from_py_ast(node)
    elif isinstance(node, ast.Constant):
        return ConstantExpression(node.value)
    elif isinstance(node, ast.Name):
        return SymbolExpression(node.id)
    else:
        raise CompilationError(f"Invalid expression {node!r}")


def annotation_to_datatype(ann: ast.expr) -> VariableType:
    match ann:
        case ast.Name(id="Score"):
            return ScoreType()
        case ast.Name(id="LocalScope"):
            return LocalScopeType(stores.AnyDataType)
        case ast.Name(id="Nbt"):
            return NbtType(stores.AnyDataType)
        case ast.Subscript(value=ast.Name(id="Nbt"), slice=ast.Name(id=type_str)):
            return NbtType(getattr(stores, type_str))
        case ast.Subscript(value=ast.Name(id="LocalScope"), slice=ast.Name(id=type_str)):
            return LocalScopeType(getattr(stores, type_str))

    raise CompilationError(f"Invalid annotation {ann!r}")


class VariableType:
    ...


class ScoreType(VariableType):
    ...


@dataclasses.dataclass
class NbtType(VariableType):
    dtype: typing.Type[stores.DataType]


@dataclasses.dataclass
class LocalScopeType(VariableType):
    dtype: typing.Type[stores.DataType]


@dataclasses.dataclass
class Function:
    statements: list[Statement]
    args: dict[str, VariableType]

    @classmethod
    def from_py_ast(cls, node: ast.FunctionDef):
        return cls(
            [statement_factory(stmt) for stmt in node.body],
            {arg.arg: annotation_to_datatype(arg.annotation) for arg in node.args.args}
        )


class Expression:
    ...


@dataclasses.dataclass
class UnaryOpExpression(Expression):
    expression: Expression
    op: typing.Literal["-"]

    @classmethod
    def from_py_ast(cls, node: ast.UnaryOp):
        breakpoint()
        return cls(
            expression_factory(node.operand),
            node.op
        )


@dataclasses.dataclass
class BinOpExpression(Expression):
    left: Expression
    right: Expression
    op: typing.Literal["+", "-", "*", "/", "%", "==", "!=", "<", ">", "<=", ">=", "and", "or"]

    @classmethod
    def from_py_ast(cls, node: ast.BoolOp | ast.Compare | ast.BinOp):
        if isinstance(node, ast.Compare):
            compile_assert(len(node.ops) == 1, f"Invalid comparison {node.ops!r}")
            left = node.left
            right = node.comparators[0]
            op = node.ops[0]
        elif isinstance(node, ast.BinOp):
            left = node.left
            right = node.right
            op = node.op
        elif isinstance(node, ast.BoolOp):
            compile_assert(len(node.values) == 2, f"Invalid boolop {node.values!r}")
            left, right = node.values
            op = node.op

        match op:
            case ast.Eq():
                op = "=="
            case ast.NotEq():
                op = "!="
            case ast.Lt():
                op = "<"
            case ast.LtE():
                op = "<="
            case ast.Gt():
                op = ">"
            case ast.GtE():
                op = ">="
            case ast.Add():
                op = "+"
            case ast.Sub():
                op = "-"
            case ast.Mult():
                op = "*"
            case ast.Div():
                op = "/"
            case ast.Mod():
                op = "%"
            case ast.And():
                op = "and"
            case ast.Or():
                op = "or"
            case _:
                raise CompilationError(f"Invalid operator {op!r}")

        return cls(
            expression_factory(left),
            expression_factory(right),
            op
        )


@dataclasses.dataclass
class FunctionCallExpression(Expression):
    function: tuple[str, ...]
    args: list[Expression]

    @classmethod
    def from_py_ast(cls, node: ast.Call):
        compile_assert(isinstance(node.func, ast.Name), f"Invalid function call {node.func!r}")
        return cls(
            (node.func.id,),
            [expression_factory(arg) for arg in node.args]
        )


@dataclasses.dataclass
class ConstantExpression(Expression):
    value: str | int | float


@dataclasses.dataclass
class SymbolExpression(Expression):
    name: str


class Statement:
    ...


@dataclasses.dataclass
class ExpressionStatement(Statement):
    expression: Expression


@dataclasses.dataclass
class WhileLoopStatement(Statement):
    condition: Expression
    body: list[Statement]


class StoppingStatement(Statement):
    ...


class ContinueStatement(StoppingStatement):
    ...


class BreakStatement(StoppingStatement):
    ...


@dataclasses.dataclass
class ReturnStatement(StoppingStatement):
    value: Expression


@dataclasses.dataclass
class IfStatement(Statement):
    condition: Expression
    true_body: list[Statement]
    false_body: list[Statement]

    @classmethod
    def from_py_ast(cls, node: ast.If):
        return cls(
            expression_factory(node.test),
            [statement_factory(stmt) for stmt in node.body],
            [statement_factory(stmt) for stmt in node.orelse]
        )


@dataclasses.dataclass
class AssignmentStatement(Statement):
    target: str
    target_type: VariableType | None
    value: Expression

    @classmethod
    def from_py_ast(cls, node: ast.Assign | ast.AnnAssign):
        if isinstance(node, ast.AnnAssign):
            target = node.target
            ann = annotation_to_datatype(node.annotation)
        else:
            compile_assert(len(node.targets) == 1, f"Invalid assignment target {node.targets!r}")
            target = node.targets[0]
            ann = None

        compile_assert(isinstance(target, ast.Name), f"Invalid assignment.")

        return cls(
            target.id,
            ann,
            expression_factory(node.value)
        )
