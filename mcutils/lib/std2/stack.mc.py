STD_RET: Score["ret"]
STD_ARG: Score["arg"]

STD_STACK_OBJECTIVE: ScoreboardObjective["stack"]
STD_STACK_INDEX_OBJECTIVE: ScoreboardObjective["index"]
STD_STACK_VALUE_OBJECTIVE: ScoreboardObjective["value"]
STD_STACK_TAG: Tag["stack"]
STD_STACK_RET_TAG: Tag["stack_ret"]
STD_STACK_RET_SEL = "@e[tag=%s, limit=1]" % (STD_STACK_RET_TAG,)


def load():
    # create the stack objective

    "scoreboard objectives add %s dummy" % (STD_STACK_INDEX_OBJECTIVE, )
    "scoreboard objectives add %s dummy" % (STD_STACK_VALUE_OBJECTIVE, )

    "say * Loaded stack library!"


def peek[stack_nr: int]():
    "tag @e remove %s" % (STD_STACK_RET_TAG, )

    # select entity
    "execute as @e[tag=%s] if score @s %s = %s %s run tag @s add %s" % (
        # execute as @e[tag=%s]
        tag_of_stack_nr[stack_nr](),

        # if score @s %s = %s %s
        STD_STACK_INDEX_OBJECTIVE,

        tag_of_stack_nr[stack_nr](),
        STD_STACK_OBJECTIVE,

        # tag @s add %s
        STD_STACK_RET_TAG
    )

    v: Score[STD_STACK_RET_SEL, STD_STACK_VALUE_OBJECTIVE]

    # return value
    STD_RET = v


def push[stack_nr: int]():
    "tag @e remove %s" % (STD_STACK_RET_TAG, )

    # summon the entity
    'summon minecraft:marker 0 0 0 {Tags:["%s", "%s", "%s"]}' % (
        tag_of_stack_nr[stack_nr](),
        STD_STACK_TAG,
        STD_STACK_RET_TAG
    )

    # increment the stack length
    "scoreboard players add %s %s 1" % (
        tag_of_stack_nr[stack_nr](),
        STD_STACK_OBJECTIVE,
    )

    # set the stack index
    entity_stack_index: Score[STD_STACK_RET_SEL, STD_STACK_INDEX_OBJECTIVE] = stack_length

    # set value
    v: Score[STD_STACK_RET_SEL, STD_STACK_VALUE_OBJECTIVE]
    v = STD_ARG


def pop[stack_nr: int]():
    peek[stack_nr]()

    # remove the entity

    "kill %s" % (STD_STACK_RET_SEL, )

    # decrement the stack length
    "scoreboard players remove %s %s 1" % (
        tag_of_stack_nr[stack_nr](),
        STD_STACK_OBJECTIVE,
    )



def main():
    load()

    STD_ARG = 42

    push[1]()
    peek[1]()
    pop[1]()