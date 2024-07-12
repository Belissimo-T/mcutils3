import decimal
import typing

from .stores import *
from ..errors import issue_warning
from ..strings import *

"""
# Conversions:

ScoreboardStore -> ScoreboardStore
 * scoreboard players operation <pl2> <ob2> = <pl1> <ob1>
 * execute store result score <pl2> <ob2> run scoreboard players get <pl1> <ob1>

ScoreboardStore -> NbtStore[number]:
 * execute store result <nbt_container_type> <nbt_container_arg> <path> <dtype> <scale> 
       run scoreboard players get <pl1> <ob1>

Const[int] -> ScoreboardStore:
 * scoreboard players set <pl1> <ob1> <const>

Const[T] -> NbtStore[T]:
 * data modify <nbt_container_type> <nbt_container_arg> <path> set value <const>

NbtStore[number | str | list | compound] -> ScoreboardStore:
 * execute store result score <pl1> <ob1> run data get <nbt_container_type> <nbt_container_arg> <path> 
   - dtype int, float or double will round down
   - dtype str, list or compound will yield length

NbtStore[T] -> NbtStore[T]:
 * data modify <nbt_container_type1> <nbt_container_arg1> <path1> 
       set from <nbt_container_type2> <nbt_container_arg2> <path2>

NbtStore[number] -> NbtStore[number <= float]:
 - check again, that it doesn't work for doubles as target
 * execute store result <nbt_container_type2> <nbt_container_arg2> <path2> <dtype2> 0.00000001 
       run data get <nbt_container_type1> <nbt_container_arg1> <path1> 100000000

NbtStore[compound | list | str] -> NbtStore[number]:
 * execute store result <nbt_container_type2> <nbt_container_arg2> <path2> <dtype2> <scale>
       run data get <nbt_container_type1> <nbt_container_arg1> <path1> 1
 - stores length of compound, list or str

NbtStore[number] -> NbtStore[compound | list | str]:
 - not sensible / impossible

NbtStore[str] -> NbtStore[list[str]]:
 - very hard, but possible

NbtStore[list[str]] -> NbtStore[str]:
 - sadly impossible
"""


def float_to_decimal(f: float) -> str:
    val = round(decimal.Decimal(f), 12).normalize()
    exp = val.as_tuple().exponent
    return f"{val:.{-exp if exp < 0 else 0}f}"


STD_TEMP_OBJECTIVE = UniqueScoreboardObjective(LiteralString("mcutils_temp"))


def score_to_score(src: ScoreboardStore, dst: ScoreboardStore) -> String:
    if src == dst:
        return Comment("scores are equal")

    return LiteralString(f"scoreboard players operation %s %s = %s %s",
                         dst.player, dst.objective, src.player, src.objective)


def score_to_nbt(src: ScoreboardStore, dst: NbtStore[NumberType], scale: float = 1) -> String:
    assert dst.dtype is not None

    return LiteralString(
        f"execute store result {dst.nbt_container_type} %s %s {dst.dtype} {float_to_decimal(scale)} "
        f"run scoreboard players get %s %s",

        dst.nbt_container_argument, dst.path,
        src.player, src.objective
    )


def const_to_score(src: ConstStore[WholeNumberType], dst: ScoreboardStore) -> String:
    return LiteralString(f"scoreboard players set %s %s {src.value}", dst.player, dst.objective)


def const_to_nbt(src: ConstStore[T_concrete], dst: NbtStore[T_concrete]) -> String:
    return LiteralString(
        f"data modify {dst.nbt_container_type} %s %s set value {src.value}",
        dst.nbt_container_argument, dst.path,
    )


def nbt_to_score(src: NbtStore, dst: ScoreboardStore, scale: float = 1) -> String:
    assert scale <= 2147483647

    return LiteralString(
        f"execute store result score %s %s run data get {src.nbt_container_type} "
        # item counting only works with omitted scale
        f"%s %s" + (f" {float_to_decimal(scale)}" if scale != 1 else ""),

        dst.player, dst.objective,
        src.nbt_container_argument, src.path,
    )


def nbt_to_same_nbt(src: NbtStore[T_concrete], dst: NbtStore[T_concrete]) -> String:
    return LiteralString(
        f"data modify {dst.nbt_container_type} %s %s "
        f"set from {src.nbt_container_type} %s %s",
        dst.nbt_container_argument, dst.path,
        src.nbt_container_argument, src.path,
    )


def nbt_number_to_nbt_number(src: NbtStore[NumberType],
                             dst: NbtStore[NumberType]) -> String:
    return nbt_to_nbt_execute_store(src, dst, scale=1e9, scale2=1e-9)


def nbt_to_nbt_execute_store(src: NbtStore[CompoundType | ListType | StringType | NumberType],
                             dst: NbtStore[NumberType],
                             scale: float | None = 1,
                             scale2: float = 1) -> String:
    assert dst.dtype is not None
    assert scale is None or scale <= 2147483647

    return LiteralString(
        f"execute store result {dst.nbt_container_type} %s %s {dst.dtype} {float_to_decimal(scale2)} "
        f"run data get {src.nbt_container_type} %s %s" + (f" {float_to_decimal(scale)}" if scale is not None else ""),
        dst.nbt_container_argument, dst.path,
        src.nbt_container_argument, src.path,
    )


def expr_to_score(src: ReadableStore, dst: ScoreboardStore, scale: float = 1) -> list[String]:
    if isinstance(src, ConstStore):
        assert scale == 1
        return [const_to_score(src, dst)]

    if isinstance(src, ScoreboardStore):
        assert scale == 1
        return [score_to_score(src, dst)]

    if isinstance(src, NbtStore):
        return [nbt_to_score(src, dst, scale)]

    raise NotImplementedError(f"Cannot store {src!r} in ScoreboardStore.")


def nbt_to_nbt(src: NbtStore, dst: NbtStore, scale: float = 1) -> list[String]:
    # For any conversion from one data type to the same data type:
    if (
        # if one of the data types is AnyDataType, we assume that the other one is the same
        src.is_data_type(AnyDataType) or dst.is_data_type(AnyDataType)
        # if the destination dtype is a supertype of the source dtype, we assume that they are the same, too
        # For example int -> Number = int -> int
        or dst.is_data_type(src.dtype_obj)
    ):
        assert scale == 1
        return [nbt_to_same_nbt(src, dst)]

    # anything else requires a conversion to a *known* data type
    if not dst.is_data_type(ConcreteDataType):
        raise CompilationError(f"Destination {dst!r} is not a concrete datatype.")

    # Number to Number:
    if src.is_data_type(NumberType) and dst.is_data_type(NumberType):
        # check for non-concrete dtype -> double conversion, because that is hard to do and not yet implemented
        if dst.is_data_type(DoubleType) and not src.is_data_type(ConcreteDataType):
            # TODO:
            #   it is possible to get the dtype of an nbt tag at runtime through
            #   put the tag in a list, then
            #   execute store success ... run data modify ... set value 1.0d
            #   this will fail if the tag is not a double
            #   then, one can just do double->double
            issue_warning(
                f"Set from {src.dtype_name} NbtStore {src} to double NbtStore {dst}: It is not possible to do type "
                f"conversion from an unknown dtype to a double without rounding to a float when using scoreboards as "
                f"an intermediate. That means a (potential) double will be rounded to a float. "
                f"In case you want to actually fetch a nbt double into another nbt double, add type "
                f"information to both NbtVars."
            )
        assert scale == 1
        return [nbt_number_to_nbt_number(src, dst)]

    # Counting items:
    if src.is_data_type(CompoundType, ListType, StringType) and dst.is_data_type(NumberType):
        assert scale == 1
        return [nbt_to_nbt_execute_store(src, dst, None)]

    raise CompilationError(f"Cannot set {src.dtype_name} NbtStore to {dst.dtype_name} NbtStore.")


def expr_to_nbt(src: ReadableStore, dst: NbtStore, scale: float = 1) -> list[String]:
    if isinstance(src, ConstStore):
        assert scale == 1
        return [const_to_nbt(src, dst)]

    if isinstance(src, ScoreboardStore):
        assert dst.is_data_type(WholeNumberType, AnyDataType)

        if not dst.is_data_type(ConcreteDataType):
            dst = dst.with_dtype(IntType)

        return [score_to_nbt(src, dst, scale)]

    if isinstance(src, NbtStore):
        return nbt_to_nbt(src, dst, scale)

    raise NotImplementedError(f"Cannot store {src!r} in NbtStore.")


def var_to_var(src: ReadableStore, dst: WritableStore, scale: float = 1) -> list[String]:
    if isinstance(dst, ScoreboardStore):
        return expr_to_score(src, dst, scale)

    if isinstance(dst, NbtStore):
        return expr_to_nbt(src, dst, scale)

    raise CompilationError(f"Cannot set {src!r} to {dst!r}.")


def add_const_to_score(src: ScoreboardStore, increment: ConstStore[NumberType]) -> list[String]:
    val = int(float(increment.value))

    if val < 0:
        return [
            LiteralString(f"scoreboard players remove %s %s {abs(val)}", src.player, src.objective)
        ]

    return [
        LiteralString(f"scoreboard players add %s %s {val}", src.player, src.objective)
    ]


def add_const(dst: WritableStore[NumberType], increment: ConstStore[NumberType]) -> list[String]:
    if isinstance(dst, ScoreboardStore):
        return add_const_to_score(dst, increment)

    if isinstance(dst, NbtStore):
        if not dst.is_data_type(NumberType, DataType):
            raise CompilationError(f"Cannot add {increment!r} to non-NumberType {dst!r}.")

        if dst.is_data_type(DoubleType, FloatType):
            temp_tag = UniqueTag(LiteralString("add_const_to_double_temp"))
            temp_sel = LiteralString("@e[tag=%s, limit=1]", temp_tag)

            return [
                # 1. summon an entity
                LiteralString('summon minecraft:marker 0 0 0 {Tags:["%s"]}', temp_tag),

                # 2. set pos
                LiteralString('data modify entity %s Pos[0] set from %s %s %s', temp_sel, *dst),

                # 3. tp by increment
                LiteralString(f"execute as %s at @s run tp @s ~{increment.value} ~ ~", temp_sel),

                # 4. read pos
                *var_to_var(NbtStore[DoubleType]("entity", temp_sel, "Pos[0]"), dst),

                # 5. kill
                LiteralString("kill @e[tag=%s]", temp_tag)
            ]
        elif dst.is_data_type(WholeNumberType):
            temp_var = ScoreboardStore("add_const_to_nbt", STD_TEMP_OBJECTIVE)
            return [
                *var_to_var(dst, temp_var),
                *add_const_to_score(temp_var, increment),
                *var_to_var(temp_var, dst),
            ]
        else:
            raise CompilationError(f"Adding to an unknown-dtype NbtStore is not supported.")

    raise CompilationError(f"Cannot add {increment!r} to {dst!r}.")


def score_score_op_in_place(dst: ScoreboardStore,
                            operation: typing.Literal["%=", "*=", "+=", "-=", "/=", "<", "=", ">", "><"],
                            src: ScoreboardStore
                            ) -> list[String]:
    return [
        LiteralString(f"scoreboard players operation %s %s %s %s %s", *dst, operation, *src)
    ]


def score_expr_op_in_place(dst: ScoreboardStore,
                           operation: typing.Literal["%=", "*=", "+=", "-=", "/=", "<", "=", ">", "><"],
                           other: ReadableStore[NumberType]) -> list[String]:
    temp_var = ScoreboardStore("score_expr_op_in_place_temp", STD_TEMP_OBJECTIVE)

    return [
        *var_to_var(other, temp_var),
        *score_score_op_in_place(dst, operation, temp_var)
    ]


def add_in_place(dst: WritableStore[NumberType], increment: ReadableStore[NumberType]) -> list[String]:
    temp_var = ScoreboardStore("add_in_place_temp", STD_TEMP_OBJECTIVE)
    temp_var2 = ScoreboardStore("add_in_place_temp2", STD_TEMP_OBJECTIVE)

    if isinstance(increment, ConstStore):
        return add_const(dst, increment)

    if isinstance(dst, ScoreboardStore):
        if isinstance(increment, ScoreboardStore):
            return score_score_op_in_place(dst, "+=", increment)

        if isinstance(increment, NbtStore):
            if not increment.is_data_type(WholeNumberType):
                raise CompilationError(f"Cannot add {increment!r} to {dst!r}. Increment must be a whole number.")

            return [
                *var_to_var(increment, temp_var),
                *score_score_op_in_place(dst, "+=", temp_var)
            ]

    if isinstance(dst, NbtStore):
        if isinstance(increment, ScoreboardStore):
            return [
                *var_to_var(dst, temp_var),
                *add_in_place(temp_var, increment),
                *var_to_var(temp_var, dst)
            ]

        if isinstance(increment, NbtStore):
            if increment.is_data_type(WholeNumberType) and dst.is_data_type(WholeNumberType):
                return [
                    *var_to_var(increment, temp_var),
                    *var_to_var(dst, temp_var2),
                    *score_score_op_in_place(temp_var2, "+=", temp_var),
                    *var_to_var(temp_var2, dst)
                ]

            raise CompilationError(f"Cannot add {increment!r} to {dst!r} yet.")

    raise CompilationError(f"Cannot add {increment!r} to {dst!r}.")


def sub_in_place(dst: WritableStore[NumberType], decrement: ReadableStore[NumberType]) -> list[String]:
    if isinstance(decrement, ConstInt):
        return add_const(dst, ConstInt(-int(decrement.value)))

    if isinstance(dst, ScoreboardStore):
        if isinstance(decrement, ScoreboardStore):
            return score_score_op_in_place(dst, "-=", decrement)

    raise CompilationError(f"Cannot subtract {decrement!r} from {dst!r}.")


def mul_const(dst: WritableStore[NumberType], factor: ConstStore[NumberType]) -> list[String]:
    if isinstance(dst, ScoreboardStore):
        return score_expr_op_in_place(dst, "*=", factor)

    raise CompilationError(f"Cannot multiply {dst!r} by {factor!r}.")


def mul_in_place(dst: WritableStore[NumberType], factor: ReadableStore[NumberType]) -> list[String]:
    if isinstance(factor, ConstStore):
        return mul_const(dst, factor)

    if isinstance(dst, ScoreboardStore):
        if isinstance(factor, ScoreboardStore):
            return score_score_op_in_place(dst, "*=", factor)

    raise CompilationError(f"Cannot multiply {factor!r} with {dst!r}.")


def div_const(dst: WritableStore[NumberType], divisor: ConstStore[NumberType]) -> list[String]:
    if isinstance(dst, ScoreboardStore):
        return score_expr_op_in_place(dst, "/=", divisor)

    raise CompilationError(f"Cannot divide {dst!r} by {divisor!r}.")


def div_in_place(dst: WritableStore[NumberType], divisor: ReadableStore[NumberType]) -> list[String]:
    if isinstance(divisor, ConstStore):
        return div_const(dst, divisor)

    if isinstance(dst, ScoreboardStore):
        if isinstance(divisor, ScoreboardStore):
            return score_score_op_in_place(dst, "/=", divisor)

    raise CompilationError(f"Cannot divide {dst!r} by {divisor!r}.")


def op_in_place(
    dst: WritableStore[NumberType],
    src: ReadableStore[NumberType],
    op: typing.Literal["+", "-", "*", "/"]
) -> list[String]:
    assert op in "+-*/"

    try:
        if op == "+":
            return add_in_place(dst, src)
        elif op == "-":
            return sub_in_place(dst, src)
        elif op == "*":
            return mul_in_place(dst, src)
        elif op == "/":
            return div_in_place(dst, src)
    except CompilationError:
        if src.is_data_type(WholeNumberType) and dst.is_data_type(WholeNumberType):
            temp_var = ScoreboardStore("op_in_place_score_tmp", STD_TEMP_OBJECTIVE)
            return [
                *var_to_var(dst, temp_var),
                *score_expr_op_in_place(temp_var, op + "=", src),
                *var_to_var(temp_var, dst)
            ]
        else:
            raise
