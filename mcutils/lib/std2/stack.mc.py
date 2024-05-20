STD_OBJECTIVE: ScoreboardObjective["mcutils"]

STD_RET: Score["ret", STD_OBJECTIVE]
STD_ARG: Score["arg", STD_OBJECTIVE]

STD_STACK_OBJECTIVE: ScoreboardObjective["stack"]
STD_STACK_INDEX_OBJECTIVE: ScoreboardObjective["index"]
STD_STACK_VALUE_OBJECTIVE: ScoreboardObjective["value"]
STD_STACK_TAG: Tag["stack"]
STD_STACK_RET_TAG: Tag["stack_ret"]
STD_STACK_RET_SEL = "@e[tag=%s, limit=1]" % (STD_STACK_RET_TAG,)


def add_scoreboard_objective[name]():
    "scoreboard objectives add %s dummy" % (name,)


def print[variable]():
    'tellraw @p {"score":{"name":"%s","objective":"%s"}}' % (
        get_player[variable](),
        get_objective[variable](),
    )


def load():
    # create the stack objective

    add_scoreboard_objective[STD_STACK_INDEX_OBJECTIVE]()
    add_scoreboard_objective[STD_STACK_VALUE_OBJECTIVE]()
    add_scoreboard_objective[STD_STACK_OBJECTIVE]()

    "say * Loaded stack library!"


def peek[stack_nr: int]():
    "tag @e remove %s" % (STD_STACK_RET_TAG,)

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
    entity_stack_index: Score[STD_STACK_RET_SEL, STD_STACK_INDEX_OBJECTIVE] = stack_length

    # set value
    v: Score[STD_STACK_RET_SEL, STD_STACK_VALUE_OBJECTIVE]
    v = STD_ARG


def pop[stack_nr: int]():
    peek[stack_nr]()

    # remove the entity
    "kill %s" % (STD_STACK_RET_SEL,)

    # decrement the stack length
    stack_length: Score[tag_of_stack_nr[stack_nr](), STD_STACK_OBJECTIVE]
    stack_length -= 1


def while_test():
    a: Score = 2

    while a:
        "say Hii"


def main():
    load()

    STD_ARG = 42

    print[STD_ARG]()

    push[1]()
    peek[1]()
    pop[1]()

    while_test()
