STD_OBJECTIVE: ScoreboardObjective["mcutils"]

STD_RET: Score["ret", STD_OBJECTIVE]
STD_ARG: Score["arg", STD_OBJECTIVE]

STD_STACK_OBJECTIVE: ScoreboardObjective["stack"]
STD_STACK_INDEX_OBJECTIVE: ScoreboardObjective["index"]
STD_STACK_VALUE_OBJECTIVE: ScoreboardObjective["value"]
STD_STACK_TAG: Tag["stack"]
STD_STACK_RET_TAG: Tag["stack_ret"]
STD_STACK_RET_SEL = "@e[tag=%s, limit=1]" % (STD_STACK_RET_TAG,)


def scoreboard_add_objective[name]():
    "scoreboard objectives add %s dummy" % (name,)


def print[msg, variable]():
    'tellraw @p ["%s", {"score":{"name":"%s","objective":"%s"}}]' % (
        msg,
        get_player[variable](),
        get_objective[variable](),
    )


def load():
    scoreboard_add_objective[STD_STACK_INDEX_OBJECTIVE]()
    scoreboard_add_objective[STD_STACK_VALUE_OBJECTIVE]()
    scoreboard_add_objective[STD_STACK_OBJECTIVE]()
    scoreboard_add_objective[STD_OBJECTIVE]()
    scoreboard_add_objective["mcutils_std"]()
    scoreboard_add_objective["mcutils_temp"]()

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
    a: Score["a", STD_OBJECTIVE] = 1

    while a < 1048577:
        # "say While Iteration!"
        print["a = ", a]()
        a *= 2
        # print["a2 = ", a]()

    "say after!"


def sum(a: Score["a", STD_OBJECTIVE], b: Score["a", STD_OBJECTIVE]):
    print["a = ", a]()
    print["b = ", b]()
    STD_ARG = a + b
    print["stdarg = ", STD_ARG]()
    push[2]()


def sum_test():
    sum(1 + 2)
    pop[2]()
    c: Score["c", STD_OBJECTIVE] = STD_RET

    print["c = ", c]()


def main():
    load()

    STD_RET = 0

    STD_ARG = 42
    print["arg=", STD_ARG]()
    push[1]()

    STD_ARG = 43
    print["arg=", STD_ARG]()
    push[1]()

    # peek[1]()
    pop[1]()
    print["ret=", STD_RET]()

    pop[1]()
    print["ret=", STD_RET]()

    while_test()
    sum_test()
    fizz_buzz()
    collatz()
    find_score_overflow()

    a[1]()


def fizz_buzz():
    i: Score["i", STD_OBJECTIVE] = 1
    div_3: Score
    div_5: Score

    while i <= 100:
        print["i=", i]()

        div_3 = i % 3 == 0
        div_5 = i % 5 == 0

        if div_3 and div_5:
            "say FizzBuzz"
        elif div_3:
            "say Fizz"
        elif div_5:
            "say Buzz"

        i += 1


def collatz():
    n: Score = 237894234

    while n != 1:
        print["n = ", n]()
        if n % 2 == 0:
            n /= 2
        else:
            n *= 3
            n += 1

    print["n = ", n]()


def find_score_overflow():
    a: Score = 1

    while a > 0:
        a *= 2
        print["a = ", a]()

    a -= 1
    print["a-1 = ", a]()
    # print["a = ", a]()

