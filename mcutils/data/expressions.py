from __future__ import annotations

import abc
import ast
import dataclasses
import typing

import mcutils.ir.tree
from . import stores_conv
from .. import strings
from ..data import stores
from ..errors import compile_assert
from ..ir import commands, blocks, tree, blocks_expr
from ..lib import std

_ARG_PRIMITIVES: dict[int, stores.NbtStore[stores.AnyDataType]] = {}
_FETCH_TEMP = stores.NbtStore[stores.AnyDataType]("storage", "mcutils:expr_temp", "fetch")


def get_temp_var(i: int) -> stores.NbtStore[stores.AnyDataType]:
    if i in _ARG_PRIMITIVES:
        return _ARG_PRIMITIVES[i]
    else:
        _ARG_PRIMITIVES[i] = stores.NbtStore("storage", "mcutils:expr_temp", f"arg{i}")
        return _ARG_PRIMITIVES[i]


def fetch(
    src: stores.ReadableStore,
    dst: stores.PrimitiveStore | None
) -> list[tree.Statement]:
    if isinstance(src, Expression):
        out = []
        for arg in src.args:
            out += [
                *fetch(arg, _FETCH_TEMP),
                blocks_expr.StackPushStatement(_FETCH_TEMP),
            ]

        temp_vars = tuple(get_temp_var(i).with_dtype(arg.dtype_obj) for i, arg in enumerate(src.args))
        for var in reversed(temp_vars):
            out.append(blocks_expr.StackPopStatement(var))

        out += src.fetch_to(tuple(temp_vars), dst)

        return out
    else:
        if dst is not None:
            return [blocks_expr.SimpleAssignmentStatement(src, dst)]


class Expression(stores.ReadableStore):
    args: tuple[stores.ReadableStore, ...]

    @abc.abstractmethod
    def fetch_to(self, args: tuple[stores.PrimitiveStore, ...], target: stores.PrimitiveStore) -> list[tree.Statement]:
        ...

    @property
    @abc.abstractmethod
    def dtype_obj(self) -> typing.Type[stores.DataType]:
        ...


@dataclasses.dataclass
class BinOpExpression(Expression):
    left: stores.ReadableStore
    op: typing.Literal["+", "-", "*", "/", "%", "==", "!=", "<", ">", "<=", ">=", "and", "or"]
    right: stores.ReadableStore

    _TEMP1: typing.ClassVar = std.get_temp_var("expr_temp1")
    _TEMP2: typing.ClassVar = std.get_temp_var("expr_temp2")
    _TEMP3: typing.ClassVar = std.get_temp_var("expr_temp3")

    @property
    def args(self):
        return self.left, self.right

    def fetch_to(self, args: tuple[stores.PrimitiveStore, ...], target: stores.PrimitiveStore) -> list[tree.Statement]:
        left, right = args
        if self.op in ("+", "-", "*", "/"):
            return [
                mcutils.ir.tree.LiteralStatement(stores_conv.op_in_place(left, right, self.op)),
                mcutils.ir.tree.LiteralStatement(stores_conv.var_to_var(left, target)),
            ]
        elif self.op in ("<", "<=", ">", ">=", "=="):
            if self.op == "==":
                op = "="
            else:
                op = self.op
            return [
                mcutils.ir.tree.LiteralStatement(stores_conv.var_to_var(left, self._TEMP1)),
                mcutils.ir.tree.LiteralStatement(stores_conv.var_to_var(right, self._TEMP2)),
                mcutils.ir.tree.LiteralStatement(stores_conv.var_to_var(stores.ConstInt(0), self._TEMP3)),
                mcutils.ir.tree.LiteralStatement([
                    strings.LiteralString(
                        f"execute if score %s %s {op} %s %s run scoreboard players set %s %s 1",
                        *self._TEMP1, *self._TEMP2, *self._TEMP3
                    )
                ]),
                mcutils.ir.tree.LiteralStatement(stores_conv.var_to_var(self._TEMP3, target)),
            ]
        elif self.op == "!=":
            return [
                mcutils.ir.tree.LiteralStatement(stores_conv.var_to_var(left, self._TEMP1)),
                mcutils.ir.tree.LiteralStatement(stores_conv.var_to_var(right, self._TEMP2)),
                mcutils.ir.tree.LiteralStatement(stores_conv.var_to_var(stores.ConstInt(1), self._TEMP3)),
                mcutils.ir.tree.LiteralStatement([
                    strings.LiteralString(
                        f"execute if score %s %s = %s %s run scoreboard players set %s %s 0",
                        *self._TEMP1, *self._TEMP2, *self._TEMP3
                    )
                ]),
                mcutils.ir.tree.LiteralStatement(stores_conv.var_to_var(self._TEMP3, target)),
            ]
        elif self.op == "%":
            return [
                mcutils.ir.tree.LiteralStatement(stores_conv.var_to_var(left, self._TEMP1)),
                mcutils.ir.tree.LiteralStatement(stores_conv.var_to_var(right, self._TEMP2)),
                mcutils.ir.tree.LiteralStatement([
                    strings.LiteralString(
                        f"scoreboard players operation %s %s %%= %s %s",
                        *self._TEMP1, *self._TEMP2
                    )
                ]),
                mcutils.ir.tree.LiteralStatement(stores_conv.var_to_var(self._TEMP1, target)),
            ]
        elif self.op == "and":
            return [
                mcutils.ir.tree.LiteralStatement(stores_conv.var_to_var(left, self._TEMP1)),
                mcutils.ir.tree.LiteralStatement(stores_conv.var_to_var(right, self._TEMP2)),
                mcutils.ir.tree.LiteralStatement([
                    strings.LiteralString(
                        f"execute unless score %s %s matches 0 unless score %s %s matches 0 run scoreboard players set %s %s 1",
                        *self._TEMP1, *self._TEMP2, *self._TEMP1
                    )
                ]),
                mcutils.ir.tree.LiteralStatement(stores_conv.var_to_var(self._TEMP1, target)),
            ]
        else:
            compile_assert(False)

    @property
    def dtype_obj(self) -> typing.Type[stores.DataType]:
        return stores.AnyDataType


def get_var_of_arg_i(i: int) -> stores.WritableStore:
    return stores.NbtStore("storage", "mcutils:expr_temp", f"arg_{i}")


RET_VALUE = stores.NbtStore("storage", "mcutils:expr_temp", "ret_value")


@dataclasses.dataclass
class FunctionCallExpression(Expression):
    function: tuple[str, ...]
    args: tuple[stores.ReadableStore, ...]
    compile_time_args: tuple[ast.Constant | ast.Name, ...]

    def fetch_to(self, args: tuple[stores.PrimitiveStore, ...], target: stores.PrimitiveStore | None) -> list[
        tree.Statement]:
        return [
            *[blocks_expr.SimpleAssignmentStatement(src, get_var_of_arg_i(i)) for i, src in enumerate(self.args)],
            blocks.FunctionCallStatementUnresolvedCtArgs(self.function, self.compile_time_args),
        ] + ([blocks_expr.SimpleAssignmentStatement(RET_VALUE, target)] if target is not None else [])

    @property
    def dtype_obj(self) -> typing.Type[stores.DataType]:
        return stores.AnyDataType
