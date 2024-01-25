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

STD_TEMP_OBJECTIVE = UniqueScoreboardObjective(LiteralString("temp"))


def score_to_score(src: ScoreboardStore, dst: ScoreboardStore) -> String:
    if src == dst:
        return Comment("scores are equal")

    return LiteralString(f"scoreboard players operation %s %s = %s %s",
                         dst.player, dst.objective, src.player, src.objective)


def score_to_nbt(src: ScoreboardStore, dst: NbtStore[NumberType], scale: float = 1) -> String:
    assert dst.dtype is not None

    return LiteralString(
        f"execute store result {dst.nbt_container_type} %s {dst.path} {dst.dtype} {scale} "
        f"run scoreboard players get %s %s",

        dst.nbt_container_argument,
        src.player, src.objective
    )


def const_to_score(src: ConstStore[WholeNumberType], dst: ScoreboardStore) -> String:
    return LiteralString(f"scoreboard players set %s %s {src.value}", dst.player, dst.objective)


def const_to_nbt(src: ConstStore[T_concrete], dst: NbtStore[T_concrete]) -> String:
    return LiteralString(
        f"data modify {dst.nbt_container_type} %s {dst.path} set value {src.value}",
        dst.nbt_container_argument
    )


def nbt_to_score(src: NbtStore, dst: ScoreboardStore, scale: float = 1) -> String:
    assert scale <= 2147483647

    return LiteralString(
        f"execute store result score %s %s run data get {src.nbt_container_type} "
        f"%s {src.path} {scale}",

        dst.player, dst.objective,
        src.nbt_container_argument
    )


def nbt_to_same_nbt(src: NbtStore[T_concrete], dst: NbtStore[T_concrete]) -> String:
    return LiteralString(
        f"data modify {dst.nbt_container_type} %s {dst.path} "
        f"set from {src.nbt_container_type} %s {src.path}",
        dst.nbt_container_argument,
        src.nbt_container_argument
    )


def nbt_number_to_nbt_number(src: NbtStore[NumberType],
                             dst: NbtStore[NumberType]) -> String:
    return nbt_to_nbt_execute_store(src, dst, scale=10e10, scale2=10e-10)


def nbt_to_nbt_execute_store(src: NbtStore[CompoundType | ListType | StringType | NumberType],
                             dst: NbtStore[NumberType],
                             scale: float = 1,
                             scale2: float = 1) -> String:
    assert dst.dtype is not None
    assert scale <= 2147483647

    return LiteralString(
        f"execute store result {dst.nbt_container_type} %s {dst.path} {dst.dtype} {scale2} "
        f"run data get {src.nbt_container_type} %s {src.path} {scale}",
        dst.nbt_container_argument,
        src.nbt_container_argument
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
        # if both are AnyDataType, we assume that they are the same
        if src.is_data_type(AnyDataType) and not dst.is_data_type(AnyDataType):
            issue_warning(f"Assuming dtype of any-dtype source {src!r} is the same as any-dtype "
                          f"destination {dst!r}.")

        if not dst.is_data_type(ConcreteDataType, AnyDataType):
            issue_warning(f"Assuming dtype of destination {dst!r} with non-concrete dtype is the "
                          f"same as source {src!r}.")

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
        return [nbt_to_nbt_execute_store(src, dst, scale)]

    raise CompilationError(f"Cannot set {src.dtype_name} NbtStore to {dst.dtype_name} NbtStore.")


def expr_to_nbt(src: ReadableStore, dst: NbtStore, scale: float = 1) -> list[String]:
    if isinstance(src, ConstStore):
        assert scale == 1
        return [const_to_nbt(src, dst)]

    if isinstance(src, ScoreboardStore):
        if not dst.is_data_type(ConcreteDataType):
            dst = NbtStore[IntType](dst.nbt_container_type, dst.nbt_container_argument, dst.path)

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


def add_const_to_score(src: ScoreboardStore, increment: ConstStore[NumberType], scale: float = 1) -> list[String]:
    val = int(int(increment.value) * scale)

    if val < 0:
        return [
            LiteralString(f"scoreboard players remove %s %s {abs(val)}", src.player, src.objective)
        ]

    return [
        LiteralString(f"scoreboard players add %s %s {val}", src.player, src.objective)
    ]


def add_const(src: WritableStore[NumberType], increment: ConstStore[NumberType]) -> list[String]:
    if isinstance(src, ScoreboardStore):
        return add_const_to_score(src, increment)

    if isinstance(src, NbtStore):
        if not src.is_data_type(NumberType, DataType):
            raise CompilationError(f"Cannot add {increment!r} to non-NumberType {src!r}.")

        if src.is_data_type(ConcreteDataType):
            if src.dtype == "double":
                temp_tag = UniqueTag(LiteralString("add_const_to_double_temp"))
                temp_sel = LiteralString("@e[tag=%s, limit=1]", temp_tag)

                return [
                    # 1. summon an entity
                    LiteralString('summon minecraft:marker 0 0 0 {Tags:["%s"]}', temp_tag),

                    # 2. set pos
                    LiteralString('data modify entity %s Pos[0] set from %s %s %s', temp_sel, *src),

                    # 3. tp by increment
                    LiteralString(f"execute as %s at @s run tp @s ~{increment.value} ~ ~", temp_sel),

                    # 4. read pos
                    *var_to_var(NbtStore[DoubleType]("entity", temp_sel, "Pos[0]"), src),

                    # 5. kill
                    LiteralString("kill %s", temp_sel)
                ]
        if src.is_data_type(WholeNumberType):
            scale = 1
        else:
            scale = 1e9

        temp_var = ScoreboardStore("add_const_to_nbt", STD_TEMP_OBJECTIVE)
        return [
            *var_to_var(src, temp_var, scale=scale),
            *add_const_to_score(temp_var, increment, scale=scale),
            *var_to_var(temp_var, src, scale=1 / scale),
        ]

        raise CompilationError(f"Adding to an unknown-dtype NbtStore is not supported yet.")

    raise CompilationError(f"Cannot add {increment!r} to {src!r}.")


def score_score_op_in_place(src: ScoreboardStore,
                            operation: typing.Literal["%=", "*=", "+=", "-=", "/=", "<", "=", ">", "><"],
                            other: ScoreboardStore
                            ) -> list[String]:
    return [
        LiteralString(f"scoreboard players operation %s %s %s %s %s", *src, operation, *other)
    ]


def score_expr_op_in_place(src: ScoreboardStore,
                           operation: typing.Literal["%=", "*=", "+=", "-=", "/=", "<", "=", ">", "><"],
                           other: ReadableStore[NumberType]) -> list[String]:
    temp_var = ScoreboardStore("score_expr_op_in_place_temp", STD_TEMP_OBJECTIVE)

    return [
        *var_to_var(other, temp_var),
        *score_score_op_in_place(src, operation, temp_var)
    ]


def add_in_place(src: WritableStore[NumberType], increment: ReadableStore[NumberType]) -> list[String]:
    temp_var = ScoreboardStore("add_in_place_temp", STD_TEMP_OBJECTIVE)
    temp_var2 = ScoreboardStore("add_in_place_temp2", STD_TEMP_OBJECTIVE)

    if isinstance(increment, ConstStore):
        return add_const(src, increment)

    if isinstance(src, ScoreboardStore):
        if isinstance(increment, ScoreboardStore):
            return score_score_op_in_place(src, "+=", increment)

        if isinstance(increment, NbtStore):
            if not increment.is_data_type(WholeNumberType):
                raise CompilationError(f"Cannot add {increment!r} to {src!r}. Increment must be a whole number.")

            return [
                *var_to_var(increment, temp_var),
                *score_score_op_in_place(src, "+=", temp_var)
            ]

    if isinstance(src, NbtStore):
        if isinstance(increment, ScoreboardStore):
            return [
                *var_to_var(src, temp_var),
                *add_in_place(temp_var, increment),
                *var_to_var(temp_var, src)
            ]

        if isinstance(increment, NbtStore):
            if increment.is_data_type(WholeNumberType) and src.is_data_type(WholeNumberType):
                return [
                    *var_to_var(increment, temp_var),
                    *var_to_var(src, temp_var2),
                    *score_score_op_in_place(temp_var2, "+=", temp_var),
                    *var_to_var(temp_var2, src)
                ]

            raise CompilationError(f"Cannot add {increment!r} to {src!r} yet.")

    raise CompilationError(f"Cannot add {increment!r} to {src!r}.")
