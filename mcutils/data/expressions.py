from __future__ import annotations

import abc
import ast
import dataclasses
import typing

from . import stores_conv, object_model
from .. import strings
from ..data import stores
from ..errors import compile_assert
from ..ir import blocks, tree, blocks_expr, tree_statements_base
from ..lib import std

_ARG_PRIMITIVES: dict[int, stores.NbtStore[stores.AnyDataType]] = {}
_FETCH_TEMP = stores.NbtStore[stores.AnyDataType]("storage", "mcutils:expr_temp", "fetch")


def get_temp_var(i: int) -> stores.NbtStore[stores.AnyDataType]:
    if i in _ARG_PRIMITIVES:
        return _ARG_PRIMITIVES[i]
    else:
        _ARG_PRIMITIVES[i] = stores.NbtStore("storage", "mcutils:expr_temp", f"tmp{i}")
        return _ARG_PRIMITIVES[i]


def fetch(
    src: stores.ReadableStore,
    dst: stores.PrimitiveWritableStore | None
) -> list[tree_statements_base.Statement]:
    if isinstance(src, ExpressionBase):
        out = []
        out2 = []
        temp_vars: list[stores.PrimitiveReadableStore] = []
        for i, arg in enumerate(src.args):
            if isinstance(arg, stores.PrimitiveReadableStore):
                temp_vars.append(arg)
            else:
                temp_var = get_temp_var(i).with_dtype(arg.dtype_obj)
                temp_vars.append(temp_var)

                out += [
                    *fetch(arg, _FETCH_TEMP),
                    tree.StackPushStatement(_FETCH_TEMP),
                ]
                out2 += [
                    tree.StackPopStatement(temp_var)
                ]

        out += reversed(out2)

        out += src.fetch_to(tuple(temp_vars), dst)

        return out
    else:
        if dst is not None:
            return [blocks_expr.SimpleAssignmentStatement(src, dst)]


class ExpressionBase(stores.ReadableStore):
    args: tuple[stores.ReadableStore, ...]

    @abc.abstractmethod
    def fetch_to(
        self,
        args: tuple[stores.PrimitiveReadableStore, ...],
        target: stores.PrimitiveWritableStore
    ) -> list[tree_statements_base.Statement]:
        ...

    @property
    @abc.abstractmethod
    def dtype_obj(self) -> typing.Type[stores.DataType]:
        ...


# @dataclasses.dataclass
# class UnaryOpExpression(ExpressionBase):
#     expr: stores.ReadableStore
#     op: typing.Literal["not", "-"]
#
#     @property
#     def args(self):
#         return self.expr,
#
#     def fetch_to(self, args: tuple[stores.PrimitiveReadableStore, ...], target: stores.PrimitiveWritableStore) -> list[
#         tree.Statement]:
#         raise NotImplementedError
#
#     @property
#     def dtype_obj(self) -> typing.Type[stores.DataType]:
#         raise NotImplementedError


@dataclasses.dataclass
class BinOpExpression(ExpressionBase):
    left: stores.ReadableStore
    op: typing.Literal["+", "-", "*", "/", "%", "==", "!=", "<", ">", "<=", ">=", "and", "or"]
    right: stores.ReadableStore

    _TEMP1: typing.ClassVar = std.get_temp_var("expr_temp1")
    _TEMP2: typing.ClassVar = std.get_temp_var("expr_temp2")
    _TEMP3: typing.ClassVar = std.get_temp_var("expr_temp3")

    @property
    def args(self):
        return self.left, self.right

    def fetch_to(
        self,
        args: tuple[stores.PrimitiveWritableStore, ...],
        target: stores.PrimitiveWritableStore
    ) -> list[tree_statements_base.Statement]:
        left, right = args
        if self.op in ("+", "-", "*", "/"):
            return [
                blocks_expr.SimpleAssignmentStatement(left, target),
                tree.LiteralStatement(stores_conv.op_in_place(target, right, self.op)),
            ]
        elif self.op in ("<", "<=", ">", ">=", "=="):
            if self.op == "==":
                op = "="
            else:
                op = self.op
            return [
                blocks_expr.SimpleAssignmentStatement(left, self._TEMP1),
                blocks_expr.SimpleAssignmentStatement(right, self._TEMP2),
                blocks_expr.SimpleAssignmentStatement(stores.ConstInt(0), self._TEMP3),
                tree.LiteralStatement([
                    strings.LiteralString(
                        f"execute if score %s %s {op} %s %s run scoreboard players set %s %s 1",
                        *self._TEMP1, *self._TEMP2, *self._TEMP3
                    )
                ]),
                blocks_expr.SimpleAssignmentStatement(self._TEMP3, target),
            ]
        elif self.op == "!=":
            return [
                blocks_expr.SimpleAssignmentStatement(left, self._TEMP1),
                blocks_expr.SimpleAssignmentStatement(right, self._TEMP2),
                blocks_expr.SimpleAssignmentStatement(stores.ConstInt(1), self._TEMP3),
                tree.LiteralStatement([
                    strings.LiteralString(
                        f"execute if score %s %s = %s %s run scoreboard players set %s %s 0",
                        *self._TEMP1, *self._TEMP2, *self._TEMP3
                    )
                ]),
                blocks_expr.SimpleAssignmentStatement(self._TEMP3, target),
            ]
        elif self.op == "%":
            return [
                blocks_expr.SimpleAssignmentStatement(left, self._TEMP1),
                blocks_expr.SimpleAssignmentStatement(right, self._TEMP2),
                tree.LiteralStatement([
                    strings.LiteralString(
                        f"scoreboard players operation %s %s %%= %s %s",
                        *self._TEMP1, *self._TEMP2
                    )
                ]),
                blocks_expr.SimpleAssignmentStatement(self._TEMP1, target),
            ]
        elif self.op == "and":
            return [
                blocks_expr.SimpleAssignmentStatement(left, self._TEMP1),
                blocks_expr.SimpleAssignmentStatement(right, self._TEMP2),
                tree.LiteralStatement([
                    strings.LiteralString(
                        f"execute unless score %s %s matches 0 unless score %s %s matches 0 run scoreboard players set %s %s 1",
                        *self._TEMP1, *self._TEMP2, *self._TEMP1
                    )
                ]),
                blocks_expr.SimpleAssignmentStatement(self._TEMP1, target),
            ]
        else:
            compile_assert(False)

    @property
    def dtype_obj(self) -> typing.Type[stores.DataType]:
        return stores.AnyDataType


@dataclasses.dataclass
class FunctionCallExpression(ExpressionBase):
    function: tuple[str, ...]
    args: tuple[stores.ReadableStore, ...]
    compile_time_args: tuple[ast.Constant | ast.Name, ...]

    def fetch_to(
        self,
        args: tuple[stores.PrimitiveWritableStore, ...],
        target: stores.PrimitiveWritableStore | None
    ) -> list[tree_statements_base.Statement]:
        return [
            *[
                blocks_expr.SimpleAssignmentStatement(src, object_model.get_var_of_arg_i(i))  #
                for i, src in enumerate(args)
            ],
            blocks.FunctionCallStatement(self.function, self.compile_time_args),
        ] + ([blocks_expr.SimpleAssignmentStatement(object_model.RET_VALUE, target)] if target is not None else [])

    @property
    def dtype_obj(self) -> typing.Type[stores.DataType]:
        return stores.AnyDataType
