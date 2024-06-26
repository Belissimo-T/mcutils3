from __future__ import annotations

import base64

import ast_comments as ast
import dataclasses
import typing

from ..data import stores
from ..errors import CompilationError, compile_assert
from .. import strings


@dataclasses.dataclass
class Scope:
    parent_scope: Scope | None = None

    variables: dict[str, VariableType] = dataclasses.field(default_factory=dict)
    strings: dict[str, strings.String] = dataclasses.field(default_factory=dict)
    pyfuncs: dict[str, typing.Callable] = dataclasses.field(default_factory=dict)
    compile_time_args: dict[str, typing.Any] = dataclasses.field(default_factory=dict)

    compile_function_template: typing.Callable[[tuple[str, ...], tuple], None] | None = None

    _ALLOWED_TYPES = typing.Literal["variable", "string", "pyfunc", "compile_time_arg"]

    def get(self, name: str, type_: _ALLOWED_TYPES | tuple[_ALLOWED_TYPES, ...]):
        try:
            if isinstance(type_, tuple):
                for t in type_:
                    try:
                        return self.get(name, t)
                    except KeyError:
                        pass
                raise KeyError(f"Undefined {type_} {name!r}.")

            if type_ == "variable":
                return self.variables[name]
            elif type_ == "string":
                return self.strings[name]
            elif type_ == "pyfunc":
                return self.pyfuncs[name]
            elif type_ == "compile_time_arg":
                return self.compile_time_args[name]
            else:
                assert False
        except KeyError as e:
            if self.parent_scope is not None:
                return self.parent_scope.get(name, type_)
            else:
                raise KeyError(f"Undefined {type_} {name!r}.") from e

    def get_compile_time_function_template(self):
        if self.compile_function_template is not None:
            return self.compile_function_template
        elif self.parent_scope is not None:
            return self.parent_scope.get_compile_time_function_template()
        else:
            raise CompilationError("No compile time function template found.")

    def collapse(self) -> Scope:
        if self.parent_scope is None:
            return self

        parent = self.parent_scope.collapse()

        return Scope(
            parent_scope=parent,
            variables={**parent.variables, **self.variables},
            strings={**parent.strings, **self.strings},
            pyfuncs={**parent.pyfuncs, **self.pyfuncs},
            compile_time_args={**parent.compile_time_args, **self.compile_time_args},
            compile_function_template=self.compile_function_template or parent.compile_function_template
        )


def compile_time_args_to_str(args: tuple) -> str:
    if not args:
        return "0"

    outs = []
    for arg in args:
        match arg:
            case int(a):
                outs.append(str(a))
            case strings.String() as s:
                outs.append(f"string_{s._id}")
            case stores.ScoreboardStore() as v:
                outs.append(
                    f"score_{v.player._id if v.player else 'no_player'}_{v.objective._id if v.objective else 'no_objective'}"
                )
            case str(s):
                outs.append(base64.b32encode(s.encode()).decode().lower().replace("=", "_"))
            case _:
                breakpoint()

    return "_".join(outs)


@dataclasses.dataclass
class File:
    function_templates: dict[tuple[str, ...], FunctionTemplate]
    scope: Scope

    @classmethod
    def from_py_ast(cls, node: ast.Module, py_library: typing.Type | None):
        scope = Scope(pyfuncs={f: getattr(py_library, f) for f in py_library.__pyfuncs__})

        function_templates = {}

        for stmt in node.body:
            match stmt:
                case ast.FunctionDef(name=name):
                    function_templates[name,] = FunctionTemplate(node=stmt)

                case ast.AnnAssign(target=ast.Name(id=name),
                                   annotation=ast.Subscript(value=ast.Name(id="ScoreboardObjective"), slice=s)):
                    scope.strings[name] = strings.UniqueScoreboardObjective(
                        parse_string(s, scope)
                    )
                case ast.AnnAssign(target=ast.Name(id=name),
                                   annotation=ast.Subscript(value=ast.Name(id="Tag"), slice=s)):
                    scope.strings[name] = strings.UniqueTag(parse_string(s, scope))
                case ast.Assign(targets=[ast.Name(id=name)], value=ast.BinOp(left=ast.Constant(value=val), op=ast.Mod(),
                                                                             right=ast.Tuple(elts=elts))):
                    scope.strings[name] = strings.LiteralString(val, *[
                        parse_string(el, scope) for el in elts
                    ])
                case ast.AnnAssign(target=ast.Name(id=name), annotation=ann):
                    scope.variables[name] = annotation_to_datatype(ann, scope)
                case ast.Comment():
                    pass
                case _:
                    raise CompilationError(f"Invalid statement {stmt!r} in namespace {ast!r}")

        return cls(function_templates, scope)


def statement_factory(node: ast.stmt, context: Scope) -> Statement:
    match node:
        case ast.Expr(value=ast.BinOp(left=ast.Constant(value=val), op=ast.Mod(), right=ast.Tuple(elts=elts))):
            return LiteralStatement([
                strings.LiteralString(val, *[
                    parse_string(el, context) for el in elts
                ])
            ])
        case ast.Expr(value=ast.Constant(value=str(val))):
            return LiteralStatement([strings.LiteralString(val)])
        case ast.Expr():
            return ExpressionStatement(expression_factory(node.value, context))
        case ast.While(test=test, body=body):
            return WhileLoopStatement(
                expression_factory(test, context),
                [statement_factory(stmt, context) for stmt in body]
            )
        case ast.If() as node:
            return IfStatement.from_py_ast(node, context)
        case ast.Assign() | ast.AnnAssign():
            return AssignmentStatement.from_py_ast(node, context)
        case ast.AugAssign() as a:
            return InPlaceOperationStatement.from_py_ast(a, context)
        case ast.Return(value=value):
            return ReturnStatement(expression_factory(value, context) if value is not None else None)
        case ast.Continue():
            return ContinueStatement()
        case ast.Break():
            return BreakStatement()
        case ast.Comment(value=v):
            return CommentStatement(v.lstrip("#").strip())
        case ast.Pass():
            return CommentStatement("pass")
        case _:
            raise CompilationError(f"Invalid statement {node!r}")


def expression_factory(node: ast.expr, context: Scope) -> Expression:
    match node:
        case ast.UnaryOp():
            return UnaryOpExpression.from_py_ast(node)
        case ast.Compare() | ast.BinOp() | ast.BoolOp():
            return BinOpExpression.from_py_ast(node, context)
        case ast.Call():
            return FunctionCallExpression.from_py_ast(node, context)
        case ast.Constant(value=value):
            return ConstantExpression(value)
        case ast.Name(id=id):
            try:
                a = context.get(id, "compile_time_arg")
                raise CompilationError(f"Currently not supported :((")
            except KeyError:
                return SymbolExpression(id)
        case _:
            raise CompilationError(f"Invalid expression {node!r}")


def annotation_to_datatype(ann: ast.expr, context: Scope) -> VariableType:
    match ann:
        case ast.Name(id="Score"):
            return ScoreType()
        case ast.Subscript(value=ast.Name(id="Score"), slice=ast.Constant() as s):
            return ScoreType(player=parse_string(s, context))
        case ast.Subscript(value=ast.Name(id="Score"), slice=ast.Tuple(elts=[s1, s2])):
            return ScoreType(player=parse_string(s1, context),
                             objective=parse_string(s2, context))
        case ast.Name(id="LocalScope"):
            return LocalScopeType(stores.AnyDataType)
        case ast.Name(id="Nbt"):
            return NbtType(stores.AnyDataType)
        case ast.Subscript(value=ast.Name(id="Nbt"), slice=ast.Name(id=type_str)):
            return NbtType(getattr(stores, type_str))
        case ast.Subscript(value=ast.Name(id="LocalScope"), slice=ast.Name(id=type_str)):
            return LocalScopeType(getattr(stores, type_str))
        case _:
            raise CompilationError(f"Invalid annotation {ann!r}")


def parse_string(expr: ast.expr, context: Scope) -> strings.String:
    match expr:
        case ast.Constant(value=val):
            return strings.LiteralString(val)
        case ast.Name(id=name):
            return context.get(name, ("string", "compile_time_arg"))
        case ast.Call(func=ast.Subscript(value=ast.Name(id=func_name), slice=s), args=[], keywords=[]):
            match s:
                case ast.Constant(value=val):
                    return context.get(func_name, "pyfunc")(val)
                case ast.Name(id=name):
                    return context.get(func_name, "pyfunc")(
                        context.get(name, ("compile_time_arg", "string", "variable")))
                case _:
                    raise CompilationError(f"Invalid compile time args {s!r}.")
        case _:
            breakpoint()


class VariableType:
    ...


class StringType(VariableType):
    ...


@dataclasses.dataclass
class ScoreType(VariableType):
    player: strings.String | None = None
    objective: strings.String | None = None


@dataclasses.dataclass
class NbtType(VariableType):
    dtype: typing.Type[stores.DataType]


@dataclasses.dataclass
class LocalScopeType(VariableType):
    dtype: typing.Type[stores.DataType]


@dataclasses.dataclass
class FunctionTemplate:
    node: ast.FunctionDef

    def get_compile_time_args(self) -> list[str]:
        return [s.name for s in self.node.type_params]


@dataclasses.dataclass
class TreeFunction:
    statements: list[Statement]
    args: dict[str, VariableType]
    scope: Scope

    @classmethod
    def from_py_ast(cls, node: ast.FunctionDef, scope: Scope):
        args = {arg.arg: annotation_to_datatype(arg.annotation, scope) for arg in node.args.args}
        scope = Scope(parent_scope=scope, variables=args.copy())
        statements = []

        for stmt in node.body:
            match stmt:
                case ast.AnnAssign(target=ast.Name(id=name), annotation=ann, value=v):
                    scope.variables[name] = annotation_to_datatype(ann, scope)
                    if v is None:
                        continue

            statements.append(statement_factory(stmt, scope))

        return cls(
            statements=statements,
            args=args,
            scope=scope
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
    def from_py_ast(cls, node: ast.BoolOp | ast.Compare | ast.BinOp, context: Scope):
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

        op = op_to_str(op)

        return cls(
            expression_factory(left, context),
            expression_factory(right, context),
            op
        )


def op_to_str(op):
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
    return op


@dataclasses.dataclass
class FunctionCallExpression(Expression):
    function: tuple[str, ...]
    compile_time_args: tuple[ast.Constant | ast.Name, ...]
    args: list[Expression]

    @classmethod
    def from_py_ast(cls, node: ast.Call, scope: Scope):
        match node.func:
            case ast.Subscript(value=ast.Name(id=name), slice=s):
                compile_time_args = []
                match s:
                    case ast.Tuple(elts=elts):
                        pass
                    case _:
                        elts = [s]

                for el in elts:
                    match el:
                        case ast.Constant() | ast.Name():
                            compile_time_args.append(el)
                        case _:
                            raise CompilationError(f"Unsupported compile time args {s!r}.")

                compile_time_args = tuple(compile_time_args)
            case ast.Name(id=name):
                compile_time_args = ()
            case _:
                raise CompilationError(f"Invalid function {node.func!r}.")

        # breakpoint()
        return cls(
            function=(name,),
            compile_time_args=compile_time_args,
            args=[expression_factory(arg, scope) for arg in node.args],
        )


@dataclasses.dataclass
class ConstantExpression(Expression):
    value: str | int | float
    # stores.ConstStore?


@dataclasses.dataclass
class SymbolExpression(Expression):
    name: str


class Statement:
    ...


@dataclasses.dataclass
class ExpressionStatement(Statement):
    expression: Expression


class NestedStatement(Statement):
    ...


@dataclasses.dataclass
class WhileLoopStatement(NestedStatement):
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
class IfStatement(NestedStatement):
    condition: Expression
    true_body: list[Statement]
    false_body: list[Statement]

    @classmethod
    def from_py_ast(cls, node: ast.If, context: Scope):
        return cls(
            expression_factory(node.test, context),
            [statement_factory(stmt, context) for stmt in node.body],
            [statement_factory(stmt, context) for stmt in node.orelse]
        )


@dataclasses.dataclass
class AssignmentStatement(Statement):
    target: str
    target_type: VariableType | None
    value: Expression

    @classmethod
    def from_py_ast(cls, node: ast.Assign | ast.AnnAssign, context: Scope):
        if isinstance(node, ast.AnnAssign):
            target = node.target
            ann = annotation_to_datatype(node.annotation, context)
        else:
            compile_assert(len(node.targets) == 1, f"Invalid assignment target {node.targets!r}")
            target = node.targets[0]
            ann = None

        compile_assert(isinstance(target, ast.Name), f"Invalid assignment.")

        return cls(
            target.id,
            ann,
            expression_factory(node.value, context)
        )


@dataclasses.dataclass
class InPlaceOperationStatement(Statement):
    target: str
    value: Expression
    op: typing.Literal["+", "-", "*", "/"]

    @classmethod
    def from_py_ast(cls, node: ast.AugAssign, context: Scope):
        return cls(
            node.target.id,
            expression_factory(node.value, context),
            op_to_str(node.op)
        )


@dataclasses.dataclass
class LiteralStatement(Statement):
    strings: list[strings.String]


@dataclasses.dataclass
class CommentStatement(Statement):
    message: str
