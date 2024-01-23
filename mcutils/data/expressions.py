from __future__ import annotations

import abc
import dataclasses
import typing

from . import stores_conv
from .. import strings
from ..data import stores
from ..errors import compile_assert
from ..ir import commands, blocks, tree, blocks_expr

_ARG_PRIMITIVES: dict[int, stores.NbtStore[stores.AnyDataType]] = {}
_FETCH_TEMP = stores.NbtStore("storage", "mcutils:expr_temp", "fetch")


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

        temp_vars = tuple(get_temp_var(i) for i in range(len(src.args)))
        for var in temp_vars:
            out.append(blocks_expr.StackPopStatement(var))

        out += src.fetch_to(tuple(temp_vars), dst)
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

    @property
    def args(self):
        return self.left, self.right

    def fetch_to(self, args: tuple[stores.PrimitiveStore, ...], target: stores.PrimitiveStore) -> list[tree.Statement]:
        left, right = args
        compile_assert(self.op == "+")
        return [
            blocks.LiteralStatement(stores_conv.add_in_place(left, right)),
            blocks.LiteralStatement(stores_conv.var_to_var(left, target)),
        ]

    @property
    def dtype_obj(self) -> typing.Type[stores.DataType]:
        return stores.AnyDataType


@dataclasses.dataclass
class FunctionCallExpression(Expression):
    function: str
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
