from commands import *

STD_OBJECTIVE: ScoreboardObjective["mcutils"]
STD_STACK_OBJECTIVE: ScoreboardObjective["stack"]
STD_STACK_INDEX_OBJECTIVE: ScoreboardObjective["index"]

STD_STACK_TAG: Tag["stack"]
STD_STACK_RET_TAG: Tag["stack_ret"]
STD_STACK_RET_SEL = "@e[tag=%s, limit=1]" % (STD_STACK_RET_TAG,)


def load():
    scoreboard_add_objective[STD_STACK_INDEX_OBJECTIVE]()
    scoreboard_add_objective[STD_STACK_OBJECTIVE]()
    scoreboard_add_objective[STD_OBJECTIVE]()
    scoreboard_add_objective["mcutils_std"]()
    scoreboard_add_objective["mcutils_temp"]()

    "say * Loaded stack library!"


def peek[stack_nr]():
    stack_length: Score[tag_of_stack_nr[stack_nr](), STD_STACK_OBJECTIVE]

    return peek_any[stack_nr, stack_length]()


def peek_any[stack_nr, index]():
    "tag @e remove %s" % (STD_STACK_RET_TAG,)

    # select entity
    "execute as @e[tag=%s] if score @s %s = %s %s run tag @s add %s" % (
        # execute as @e[tag=%s]
        tag_of_stack_nr[stack_nr](),

        # if score @s %s = %s %s
        STD_STACK_INDEX_OBJECTIVE,

        get_player[index](),
        get_objective[index](),

        # tag @s add %s
        STD_STACK_RET_TAG
    )

    v: EntityData[STD_STACK_RET_SEL, "data.value"]

    return v


def push[stack_nr](value: Any):
    "tag @e remove %s" % (STD_STACK_RET_TAG,)

    # summon the entity
    'summon minecraft:marker 0 0 0 {Tags:["%s", "%s", "%s"]}' % (
        tag_of_stack_nr[stack_nr](),
        STD_STACK_TAG,
        STD_STACK_RET_TAG
    )

    stack_length: Score[tag_of_stack_nr[stack_nr](), STD_STACK_OBJECTIVE]

    # increment the stack length
    stack_length += 1

    # set the stack index
    i: Score[STD_STACK_RET_SEL, STD_STACK_INDEX_OBJECTIVE] = stack_length

    # set value
    v: EntityData[STD_STACK_RET_SEL, "data.value"] = value


def pop[stack_nr]():
    peek[stack_nr]()

    # remove the entity
    "kill %s" % (STD_STACK_RET_SEL,)

    # decrement the stack length
    stack_length: Score[tag_of_stack_nr[stack_nr](), STD_STACK_OBJECTIVE]
    stack_length -= 1


def _pop_any[stack_nr, index]():
    peek_any[stack_nr, index]()

    # remove the entity
    "kill %s" % (STD_STACK_RET_SEL,)


def exists[stack_nr: int, index]():
    peek_any[stack_nr, index]()

    out: Score = 0

    "execute if entity %s run scoreboard players set %s %s 1" % (
        STD_STACK_RET_SEL,
        get_player[out](),
        get_objective[out]()
    )

    return out
