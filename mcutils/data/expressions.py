from __future__ import annotations

import abc
import dataclasses
import typing

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
    dst: stores.PrimitiveStore
) -> list[tree.Statement]:
    if isinstance(src, Expression):
        out = []
        for arg in src.args:
            out += [
                *fetch(arg, _FETCH_TEMP),
                blocks_expr.StackPushStatement(_FETCH_TEMP),
            ]

        temp_vars = tuple(get_temp_var(i).with_dtype(arg.dtype_obj) for i, arg in enumerate(src.args))
        for var in temp_vars:
            out.append(blocks_expr.StackPopStatement(var))

        out += src.fetch_to(tuple(temp_vars), dst)

        return out
    else:
        return [blocks.LiteralStatement(stores_conv.var_to_var(src, dst))]


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

    @property
    def args(self):
        return self.left, self.right

    def fetch_to(self, args: tuple[stores.PrimitiveStore, ...], target: stores.PrimitiveStore) -> list[tree.Statement]:
        left, right = args
        if self.op == "+":
            return [
                blocks.LiteralStatement(stores_conv.add_in_place(left, right)),
                blocks.LiteralStatement(stores_conv.var_to_var(left, target)),
            ]
        elif self.op in ("<", "<=", ">", ">=", "=="):
            if self.op == "==":
                op = "="
            else:
                op = self.op
            return [
                blocks.LiteralStatement(stores_conv.var_to_var(left, self._TEMP1)),
                blocks.LiteralStatement(stores_conv.var_to_var(right, self._TEMP2)),
                blocks.LiteralStatement([
                    strings.LiteralString(
                        f"execute if score %s {op} %s run scoreboard players set %s 1",
                        *self._TEMP1, *self._TEMP2, *self._TEMP1
                    )
                ]),
                blocks.LiteralStatement(stores_conv.var_to_var(self._TEMP1, target)),
            ]
        else:
            compile_assert(False)

    @property
    def dtype_obj(self) -> typing.Type[stores.DataType]:
        return stores.AnyDataType


@dataclasses.dataclass
class FunctionCallExpression(Expression):
    function: tuple[str, ...]
    args: tuple[stores.ReadableStore, ...]
    compile_time_args: typing.Any

    def fetch_to(self, args: tuple[stores.PrimitiveStore, ...], target: stores.PrimitiveStore) -> list[tree.Statement]:
        return [
            *[blocks_expr.StackPushStatement(arg) for arg in args],
            blocks.FunctionCallStatement(self.function, self.compile_time_args)
        ]

    @property
    def dtype_obj(self) -> typing.Type[stores.DataType]:
        return stores.AnyDataType