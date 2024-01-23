from ..data import stores, stores_conv
from ..ir import commands
from ..lib import tools
from ..strings import *
from .std import STD_OBJECTIVE, STD_RET, STD_TAG, STD_ARG

STD_STACK_INDEX_OBJECTIVE = UniqueScoreboardObjective(LiteralString("index"))
STD_STACK_VALUE_OBJECTIVE = UniqueScoreboardObjective(LiteralString("value"))
STD_STACK_TAG = UniqueTag(LiteralString("stack"))
std_stack_ret_tag = UniqueTag(LiteralString("temp"))
STD_STACK_RET_SEL = LiteralString("@e[tag=%s]", std_stack_ret_tag)

load_func = commands.McFunction([
    Comment("create the stack objective"),
    LiteralString("scoreboard objectives add %s dummy", STD_STACK_INDEX_OBJECTIVE),
    LiteralString("scoreboard objectives add %s dummy", STD_STACK_VALUE_OBJECTIVE),

    *tools.log("mcutils_reborn", " * Loaded stack library!")
])

_STD_STACK_TAGS = {}


def tag_of_stacknr(stacknr: int):
    if stacknr not in _STD_STACK_TAGS:
        _STD_STACK_TAGS[stacknr] = UniqueTag(LiteralString(f"stack{stacknr}"))

    return _STD_STACK_TAGS[stacknr]


def stack_len_of_stacknr(stacknr: int):
    return stores.ScoreboardStore(tag_of_stacknr(stacknr), STD_OBJECTIVE)


def std_stack_peek(stack_nr: int) -> list[String]:
    return [
        LiteralString("tag @e remove %s", std_stack_ret_tag),

        Comment("select entity"),
        LiteralString("execute as @e[tag=%s] if score @s %s = %s %s run tag @s add %s",
                      tag_of_stacknr(stack_nr), STD_STACK_INDEX_OBJECTIVE, *stack_len_of_stacknr(stack_nr),
                      std_stack_ret_tag),

        Comment("return value"),
        *stores_conv.var_to_var(stores.ScoreboardStore(STD_STACK_RET_SEL, STD_STACK_VALUE_OBJECTIVE), STD_RET),
    ]


def std_stack_push(stack_nr: int) -> list[String]:
    return [
        LiteralString("tag @e remove %s", std_stack_ret_tag),

        Comment("summon the entity"),
        LiteralString('summon minecraft:marker 0 0 0 {Tags:["%s", "%s", "%s", "%s"]}',
                      tag_of_stacknr(stack_nr), STD_STACK_TAG, STD_TAG, std_stack_ret_tag),

        Comment("increment the stack length"),
        LiteralString("scoreboard players add %s %s 1", *stack_len_of_stacknr(stack_nr)),

        Comment("set the stack index"),
        LiteralString("scoreboard players operation %s %s = %s %s",
                      STD_STACK_RET_SEL, STD_STACK_INDEX_OBJECTIVE, *stack_len_of_stacknr(stack_nr)),

        Comment("set value"),
        *stores_conv.var_to_var(STD_ARG, stores.ScoreboardStore(STD_STACK_RET_SEL, STD_STACK_VALUE_OBJECTIVE)),
    ]


def std_stack_pop(stack_nr: int) -> list[String]:
    return [
        *std_stack_peek(stack_nr=stack_nr),

        Comment("remove the entity"),
        LiteralString("kill %s", STD_STACK_RET_SEL),

        Comment("decrement the stack length"),
        LiteralString("scoreboard players remove %s %s 1", *stack_len_of_stacknr(stack_nr)),
    ]
