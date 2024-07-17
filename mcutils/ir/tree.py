from __future__ import annotations

import base64
import dataclasses
import itertools
import typing

import ast_comments as ast

from .tree_statements_base import Statement, StoppingStatement, ContinueStatement, BreakStatement
from ..data import stores, object_model, expressions
from ..errors import CompilationError, compile_assert
from .. import strings, nbt


@dataclasses.dataclass
class Scope:
    parent_scope: Scope | None = None

    variable_types: dict[str, VariableType] = dataclasses.field(default_factory=dict)
    variables: dict[str, stores.ReadableStore | stores.WritableStore] = dataclasses.field(default_factory=dict)
    strings_: dict[str, strings.String] = dataclasses.field(default_factory=dict)
    pyfuncs: dict[str, typing.Callable] = dataclasses.field(default_factory=dict)
    compile_time_args: dict[str, typing.Any] = dataclasses.field(default_factory=dict)

    _ALLOWED_TYPES = typing.Literal["variable_type", "string", "pyfunc", "compile_time_arg", "variable"]

    def get(self, name: str, type_: _ALLOWED_TYPES | tuple[_ALLOWED_TYPES, ...]):
        try:
            if isinstance(type_, tuple):
                for t in type_:
                    try:
                        return self.get(name, t)
                    except KeyError:
                        pass
                raise KeyError(f"Undefined {type_} {name!r}.")

            if type_ == "variable_type":
                return self.variable_types[name]
            elif type_ == "variable":
                return self.variables[name]
            elif type_ == "string":
                return self.strings_[name]
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

    def collapse(self) -> Scope:
        if self.parent_scope is None:
            return self

        parent = self.parent_scope.collapse()

        return Scope(
            parent_scope=None,
            variable_types=parent.variable_types | self.variable_types,
            variables=parent.variables | self.variables,
            strings_=parent.strings_ | self.strings_,
            pyfuncs=parent.pyfuncs | self.pyfuncs,
            compile_time_args=parent.compile_time_args | self.compile_time_args,
        )

    def contains(self, name: str, type_: _ALLOWED_TYPES | tuple[_ALLOWED_TYPES, ...]) -> bool:
        try:
            self.get(name, type_)
            return True
        except KeyError:
            return False

    def add(
        self,
        variable_types: dict[str, VariableType] = None,
        variables: dict[str, stores.ReadableStore | stores.WritableStore] = None,
        strings_: dict[str, strings.String] = None, pyfuncs: dict[str, typing.Callable] = None,
        compile_time_args: dict[str, typing.Any] = None
    ):
        if variable_types is not None:
            self.variable_types.update(variable_types)
        if variables is not None:
            self.variables.update(variables)
        if strings_ is not None:
            self.strings_.update(strings_)
        if pyfuncs is not None:
            self.pyfuncs.update(pyfuncs)
        if compile_time_args is not None:
            self.compile_time_args.update(compile_time_args)


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
                    f"score_{v.player._id}_{v.objective._id}"
                )
            case stores.NbtStore() as v:
                outs.append((
                    f"nbt_{v.nbt_container_type}_"
                    f"{v.nbt_container_argument if isinstance(v.nbt_container_argument, str) else v.nbt_container_argument._id}_"
                    f"{v.path if isinstance(v.path, str) else v.path._id}"
                ))
            case str(s):
                outs.append(base64.b32encode(s.encode()).decode().lower().replace("=", "_"))
            case _:
                breakpoint()

    return "_".join(outs)


@dataclasses.dataclass(frozen=True)
class ImportSpecifier:
    level: int
    path: tuple[str, ...]

    @classmethod
    def from_module_name(cls, name: str, level: int) -> ImportSpecifier:
        return cls(level, tuple(name.split(".")))


@dataclasses.dataclass
class File:
    function_templates: dict[tuple[str, ...], FunctionTemplate]
    scope: Scope
    imports: dict[ImportSpecifier, tuple[str, ...]]
    path: tuple[str, ...]

    @classmethod
    def from_py_ast(cls, node: ast.Module, py_library: object, path: tuple[str, ...]):
        scope = Scope(pyfuncs={f: getattr(py_library, f) for f in py_library.__pyfuncs__})

        imports = {}

        function_templates = {}

        for stmt in node.body:
            match stmt:
                case ast.FunctionDef(name=name):
                    function_templates[name,] = FunctionTemplate(node=stmt)

                case ast.AnnAssign(target=ast.Name(id=name),
                                   annotation=ast.Subscript(value=ast.Name(id="ScoreboardObjective"), slice=s)):
                    scope.strings_[name] = strings.UniqueScoreboardObjective(
                        parse_string(s, scope)
                    )
                case ast.AnnAssign(target=ast.Name(id=name),
                                   annotation=ast.Subscript(value=ast.Name(id="Tag"), slice=s)):
                    scope.strings_[name] = strings.UniqueTag(parse_string(s, scope))
                case ast.Assign(targets=[ast.Name(id=name)], value=ast.BinOp(left=ast.Constant(value=val), op=ast.Mod(),
                                                                             right=ast.Tuple(elts=elts))):
                    scope.strings_[name] = strings.LiteralString(val, *[
                        parse_string(el, scope) for el in elts
                    ])
                case ast.AnnAssign(target=ast.Name(id=name), annotation=ann):
                    scope.variable_types[name] = parse_annotation(ann, scope)
                case ast.Comment():
                    pass
                case ast.Import(names=[ast.alias(name=name, asname=None)]):
                    imports[ImportSpecifier.from_module_name(name, 0)] = ()
                case ast.Import(names=[ast.alias(name=name, asname=asname)]):
                    imports[ImportSpecifier.from_module_name(name, 0)] = asname,
                case ast.ImportFrom(module=module, level=level, names=[ast.alias(name="*")]):
                    imports[ImportSpecifier.from_module_name(module, level)] = ()
                # case ast.ImportFrom(module=module, level=level, names=[ast.alias(name=name, asname=asname)]):
                #     imports[ImportSpecifier.from_module_name(module + (name,), level)] = asname,
                case _:
                    raise CompilationError(f"Invalid statement: {ast.unparse(stmt)}")

        scope.add(variables=TreeFunction.assign_symbols(scope.variable_types))

        return cls(function_templates, scope, imports, path)


def _parse_statement(node: ast.stmt, context: Scope) -> list[Statement]:
    match node:
        case ast.Expr(value=ast.BinOp(left=ast.Constant(value=val), op=ast.Mod(), right=ast.Tuple(elts=elts))):
            return [LiteralStatement([
                strings.LiteralString(val, *[
                    parse_string(el, context) for el in elts
                ])
            ])]
        case ast.Expr(value=ast.Constant(value=str(val))):
            return [LiteralStatement([strings.LiteralString(val)])]
        case ast.Expr():
            return [AssignmentStatement(parse_expression(node.value, context), None)]
        case ast.While(test=test, body=body):
            return [WhileLoopStatement(
                parse_expression(test, context),
                [x for stmt in body for x in parse_statement(stmt, context)]
            )]
        case ast.If() as node:
            return [IfStatement.from_py_ast(node, context)]
        case ast.Assign(value=v) | ast.AnnAssign(value=v) if v is not None:
            return [AssignmentStatement.from_py_ast(node, context)]
        case ast.Assign() | ast.AnnAssign():
            return []
        case ast.AugAssign() as a:
            return [InPlaceOperationStatement.from_py_ast(a, context)]
        case ast.Return(value=value):
            return [ReturnStatement(parse_expression(value, context) if value is not None else None)]
        case ast.Continue():
            return [ContinueStatement()]
        case ast.Break():
            return [BreakStatement()]
        case ast.Comment(value=v):
            return [CommentStatement(v.lstrip("#").strip())]
        case ast.Pass():
            return [CommentStatement("pass")]
        case _:
            raise CompilationError(f"Invalid statement {node!r}")


def parse_statement(node: ast.stmt, context: Scope) -> list[Statement]:
    return (
        [CommentStatement(ast.unparse(node))] +
        _parse_statement(node, context)
    )


def parse_expression(node: ast.expr, context: Scope) -> stores.ReadableStore:
    try:
        var_type = parse_annotation(node, context)
    except CompilationError:
        pass
    else:
        match var_type:
            case ScoreType(player=player, objective=objective) if player is not None is not objective:
                return stores.ScoreboardStore(
                    player=player,
                    objective=objective
                )
            case NbtType(dtype=dtype, type=type_, arg=arg,
                         path=path) if type_ is not None and arg is not None and path is not None:
                return stores.NbtStore[dtype](type_, arg, path)
            case _:
                raise CompilationError(f"Invalid expression {ast.unparse(node)}")

    match node:
        case ast.UnaryOp(op=ast.USub(), operand=ast.Constant(value=val)):
            return stores.ConstInt(-val)
        case ast.UnaryOp():
            return parse_unary_op(node)
        case ast.Compare() | ast.BinOp() | ast.BoolOp():
            return parse_binop(node, context)
        case ast.Call():
            return parse_func_call(node, context)
        case ast.Name(id=id):
            try:
                return context.get(id, "variable")
            except KeyError:
                pass

            try:
                compile_time_arg = context.get(id, "compile_time_arg")
            except KeyError:
                raise CompilationError(f"Unresolved identifier {id!r}.")
            else:
                try:
                    match compile_time_arg:
                        case int():
                            return stores.ConstInt(compile_time_arg)
                        case _:
                            return stores.ConstStore(nbt.dumps(compile_time_arg))
                except TypeError as e:
                    raise CompilationError(f"Invalid expression {node!r}") from e
        case _:
            try:
                v = ast.literal_eval(node)
                match v:
                    case int():
                        return stores.ConstInt(v)
                    case _:
                        return stores.ConstStore(nbt.dumps(v))
            except ValueError as e:
                raise CompilationError(f"Invalid expression {ast.unparse(node)}") from e


def parse_value(node: ast.expr, context: Scope):
    match node:
        case ast.Name(id=id):
            try:
                return context.get(id, ("string", "pyfunc", "compile_time_arg", "variable"))
            except KeyError:
                pass
        case _:
            try:
                return ast.literal_eval(node)
            except ValueError:
                pass

            try:
                return parse_expression(node, context)
            except CompilationError:
                pass

            try:
                return parse_string(node, context)
            except CompilationError:
                pass


def unpack_annotation(node: ast.expr) -> tuple[type[stores.DataType], ast.expr | None]:
    types_by_name = {
        "Any": stores.AnyDataType,
        "Number": stores.NumberType,
        "WholeNumber": stores.WholeNumberType,
        "Byte": stores.ByteType,
        "Short": stores.ShortType,
        "Int": stores.IntType,
        "Long": stores.LongType,
        "RealNumber": stores.RealNumberType,
        "Double": stores.DoubleType,
        "Float": stores.FloatType,
        "String": stores.StringType,
        "List": stores.ListType,
        "Compound": stores.CompoundType,
    }

    match node:
        case ast.Subscript(value=ast.Name(id=name), slice=ast.Subscript() | ast.Name() as inner):
            try:
                return types_by_name[name], inner
            except KeyError as e:
                raise CompilationError(f"Invalid type {ast.unparse(node)!r}") from e
        case ast.Name(id=name) if name in types_by_name:
            return types_by_name[name], None
        case _:
            return stores.AnyDataType, node


def parse_annotation(ann: ast.expr, context: Scope) -> VariableType:
    dtype, ann = unpack_annotation(ann)

    match ann:
        case ast.Name(id="Score"):
            compile_assert(issubclass(dtype, stores.IntType) or dtype is stores.AnyDataType)
            return ScoreType()
        case ast.Subscript(value=ast.Name(id="Score"), slice=ast.Constant() as s):
            compile_assert(issubclass(dtype, stores.IntType) or dtype is stores.AnyDataType)
            return ScoreType(player=parse_string(s, context))
        case ast.Subscript(value=ast.Name(id="Score"), slice=ast.Tuple(elts=[s1, s2])):
            compile_assert(issubclass(dtype, stores.IntType) or dtype is stores.AnyDataType)
            return ScoreType(player=parse_string(s1, context),
                             objective=parse_string(s2, context))

        case ast.Name(id="LocalScope"):
            return LocalScopeType(dtype)

        case None:
            return UnspecifiedVariableType(dtype)

        case ast.Subscript(value=ast.Name(id="StorageData"), slice=ast.Tuple(elts=[
            name_str,
            ast.Constant(value=str(path))
        ])):
            return NbtType(dtype, "storage", parse_string(name_str, context), path)
        case ast.Subscript(value=ast.Name(id="EntityData"), slice=ast.Tuple(elts=[
            selector_str,
            ast.Constant(value=str(path))
        ])):
            return NbtType(dtype, "entity", parse_string(selector_str, context), path)
        case ast.Subscript(value=ast.Name(id="BlockData"), slice=ast.Tuple(elts=[
            location_str,
            ast.Constant(value=str(path))
        ])):
            return NbtType(dtype, "block", parse_string(location_str, context), path)
        case ast.Name(id="Nbt"):
            return NbtType(dtype)

        case _:
            raise CompilationError(f"Invalid annotation {ast.unparse(ann)}.")


def parse_string(expr: ast.expr, context: Scope) -> strings.String:
    match expr:
        case ast.Constant(value=val):
            return strings.LiteralString(val)
        case ast.Name(id=name):
            try:
                return context.get(name, "string")
            except KeyError:
                pass

            try:
                val = context.get(name, "compile_time_arg")
                match val:
                    case str(val):
                        return strings.LiteralString(val)
                    case strings.String():
                        return val
                    case _:
                        raise CompilationError(
                            f"Compile-time arg {name!r} with value {val!r} cannot be interpreted as a string.")
            except KeyError:
                pass

            raise CompilationError(f"Unresolved string {name!r}.")
        case ast.Call(func=ast.Subscript(value=ast.Name(id=func_name), slice=s), args=[], keywords=[]):
            match s:
                case ast.Tuple(elts=elts):
                    args = [parse_value(el, context) for el in elts]
                case _:
                    args = [parse_value(s, context)]

            return context.get(func_name, "pyfunc")(*args)
        case _:
            breakpoint()


class VariableType:
    ...


class StringType(VariableType):
    ...


@dataclasses.dataclass
class UnspecifiedVariableType(VariableType):
    dtype: typing.Type[stores.DataType]


@dataclasses.dataclass
class ScoreType(VariableType):
    player: strings.String | None = None
    objective: strings.String | None = None


@dataclasses.dataclass
class NbtType(VariableType):
    dtype: typing.Type[stores.DataType]
    type: typing.Literal["block", "entity", "storage"] | None = None
    arg: strings.String | None = None
    path: str | None = None


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
    args: tuple[str, ...]
    scope: Scope

    @classmethod
    def from_py_ast(cls, node: ast.FunctionDef, scope: Scope):
        args = {
            arg.arg: object_model.get_var_of_arg_i(i).with_dtype(unpack_annotation(arg.annotation)[0])
            for i, arg in enumerate(node.args.args)
        }
        scope = Scope(parent_scope=scope, variables=args)

        cls.search_for_var_types(node.body, scope)
        scope.add(variables=cls.assign_symbols(scope.variable_types))

        statements = []
        for stmt in node.body:
            statements += parse_statement(stmt, scope)

        return cls(
            statements=statements,
            args=tuple(args.keys()),
            scope=scope
        )

    @classmethod
    def search_for_var_types(cls, statements: list[ast.stmt], scope: Scope):
        for statement in statements:
            match statement:
                case ast.AnnAssign(target=ast.Name(id=name), annotation=ann):
                    scope.variable_types[name] = parse_annotation(ann, scope)
                case ast.Assign(targets=[ast.Name(id=name)]):
                    if name not in scope.variable_types:
                        scope.variable_types[name] = UnspecifiedVariableType(stores.AnyDataType)
                case ast.If(test=test, body=body, orelse=orelse):
                    cls.search_for_var_types(body, scope)
                    cls.search_for_var_types(orelse, scope)
                case ast.While(test=test, body=body):
                    cls.search_for_var_types(body, scope)
                case _:
                    pass

    @classmethod
    def assign_symbols(cls, var_types: dict[str, VariableType]):
        symbols = {}

        for name, var_type in var_types.items():
            symbols[name] = cls.get_store_from_variable_type(name, var_type)

        return symbols

    @classmethod
    def get_store_from_variable_type(
        cls,
        name: str,
        var_type: VariableType,
    ) -> stores.ReadableStore | stores.WritableStore:
        match var_type:
            case ScoreType(player=None, objective=None):
                return object_model.get_temp_var("__var_" + name)
            case ScoreType(player=None, objective=obj):
                return stores.ScoreboardStore(
                    strings.UniqueScoreboardPlayer(strings.LiteralString("__var_" + name)),
                    obj
                )
            case ScoreType(player=player, objective=None):
                return stores.ScoreboardStore(player, object_model.MCUTILS_STD_OBJECTIVE)
            case ScoreType(player=player, objective=obj):
                return stores.ScoreboardStore(player, obj)
            case UnspecifiedVariableType(dtype=dtype):
                if dtype is stores.IntType:
                    return cls.get_store_from_variable_type(name, ScoreType())
                else:
                    return cls.get_store_from_variable_type(name, NbtType(dtype=dtype))
            case NbtType(dtype=dtype, type=type_, arg=arg, path=path):
                if type_ is None:
                    type_ = "storage"
                    arg = strings.LiteralString("mcutils:temp")
                    path = strings.LiteralString("vars.%s", strings.UniqueNbtVariable(strings.LiteralString(name)))

                return stores.NbtStore[dtype](type_, arg, path)
            case LocalScopeType():
                compile_assert(False)
                # scope.return stores.LocalScopeStore(var_type.dtype)
            case _:
                raise CompilationError(f"Invalid variable type {var_type!r}.")


def parse_unary_op(node: ast.UnaryOp):
    breakpoint()
    raise NotImplementedError
    return expressions.UnaryOpExpression(
        expr=parse_expression(node.operand),
        op=node.op
    )


def parse_binop(node: ast.BoolOp | ast.Compare | ast.BinOp, context: Scope):
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
    else:
        breakpoint()

    op = op_to_str(op)

    return expressions.BinOpExpression(
        left=parse_expression(left, context),
        op=op,
        right=parse_expression(right, context),
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


def parse_func_call(node: ast.Call, scope: Scope):
    match node.func:
        case ast.Subscript(value=ast.Name(id=name), slice=s):
            match s:
                case ast.Tuple(elts=elts):
                    pass
                case _:
                    elts = [s]

            compile_time_args = tuple(parse_value(el, scope) for el in elts)
        case ast.Name(id=name):
            compile_time_args = ()
        case _:
            raise CompilationError(f"Invalid function {node.func!r}.")

    return expressions.FunctionCallExpression(
        function=(name,),
        compile_time_args=compile_time_args,
        args=tuple(parse_expression(arg, scope) for arg in node.args),
    )


class NestedStatement(Statement):
    ...


@dataclasses.dataclass
class WhileLoopStatement(NestedStatement):
    condition: stores.ReadableStore
    body: list[Statement]


@dataclasses.dataclass
class ReturnStatement(StoppingStatement):
    value: stores.ReadableStore | None


@dataclasses.dataclass
class IfStatement(NestedStatement):
    condition: stores.ReadableStore | None
    true_body: list[Statement]
    false_body: list[Statement]

    @classmethod
    def from_py_ast(cls, node: ast.If, context: Scope):
        return cls(
            parse_expression(node.test, context),
            [x for stmt in node.body for x in parse_statement(stmt, context)],
            [x for stmt in node.orelse for x in parse_statement(stmt, context)]
        )


@dataclasses.dataclass
class AssignmentStatement(Statement):
    src: stores.ReadableStore
    dst: stores.WritableStore | None

    @classmethod
    def from_py_ast(cls, node: ast.Assign | ast.AnnAssign, context: Scope):
        if isinstance(node, ast.AnnAssign):
            target = node.target
        else:
            compile_assert(len(node.targets) == 1, f"Invalid assignment target {node.targets!r}")
            target = node.targets[0]

        compile_assert(isinstance(target, ast.Name), f"Invalid assignment.")

        return cls(
            parse_expression(node.value, context),
            context.get(target.id, "variable"),
        )


@dataclasses.dataclass
class InPlaceOperationStatement(Statement):
    dst: stores.WritableStore
    src: stores.ReadableStore
    op: typing.Literal["+", "-", "*", "/"]

    @classmethod
    def from_py_ast(cls, node: ast.AugAssign, context: Scope):
        return cls(
            dst=context.get(node.target.id, "variable"),
            src=parse_expression(node.value, context),
            op=op_to_str(node.op)
        )


@dataclasses.dataclass
class LiteralStatement(Statement):
    strings: list[strings.String]


@dataclasses.dataclass
class CommentStatement(Statement):
    message: strings.String | str


@dataclasses.dataclass
class StackPushStatement(Statement):
    src: stores.ReadableStore


@dataclasses.dataclass
class StackPopStatement(Statement):
    dst: stores.WritableStore
