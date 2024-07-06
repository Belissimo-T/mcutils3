STD_OBJECTIVE: ScoreboardObjective["mcutils"]

STD_ARG: Nbt[AnyDataType, "storage", "mcutils:std", "arg"]
STD_RET: Nbt[AnyDataType, "storage", "mcutils:std", "ret"]
# STD_ARG: Score["arg", STD_OBJECTIVE]
# STD_RET: Score["ret", STD_OBJECTIVE]

STD_STACK_OBJECTIVE: ScoreboardObjective["stack"]
STD_STACK_INDEX_OBJECTIVE: ScoreboardObjective["index"]
STD_STACK_VALUE_OBJECTIVE: ScoreboardObjective["value"]
STD_STACK_TAG: Tag["stack"]
STD_STACK_RET_TAG: Tag["stack_ret"]
STD_STACK_RET_SEL = "@e[tag=%s, limit=1]" % (STD_STACK_RET_TAG,)


def print_var[name, var]():
    print[name, {"color": "gray"}, " = ", {"color": "gold"}, var]()


def gamerule[rule, value]():
    "gamerule %s %s" % (rule, value)


def gamerule_max_command_chain_length[value]():
    gamerule["maxCommandChainLength", value]()


def scoreboard_add_objective[name]():
    "scoreboard objectives add %s dummy" % (name,)


def load():
    scoreboard_add_objective[STD_STACK_INDEX_OBJECTIVE]()
    scoreboard_add_objective[STD_STACK_VALUE_OBJECTIVE]()
    scoreboard_add_objective[STD_STACK_OBJECTIVE]()
    scoreboard_add_objective[STD_OBJECTIVE]()
    scoreboard_add_objective["mcutils_std"]()
    scoreboard_add_objective["mcutils_temp"]()

    "say * Loaded stack library!"


def peek[stack_nr: int]():
    stack_length: Score[tag_of_stack_nr[stack_nr](), STD_STACK_OBJECTIVE]

    peek_any[stack_nr, stack_length]()


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

    v: Nbt[AnyDataType, "entity", STD_STACK_RET_SEL, "data.value"]

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
    v: Nbt[AnyDataType, "entity", STD_STACK_RET_SEL, "data.value"]
    v = STD_ARG


def pop[stack_nr: int]():
    peek[stack_nr]()

    # remove the entity
    "kill %s" % (STD_STACK_RET_SEL,)

    # decrement the stack length
    stack_length: Score[tag_of_stack_nr[stack_nr](), STD_STACK_OBJECTIVE]
    stack_length -= 1


def exists[stack_nr: int, index]():
    peek_any[stack_nr, index]()

    # TODO
    out: Score["std_stack_exists_out", STD_OBJECTIVE] = 0

    "execute if entity %s run scoreboard players set %s %s 1" % (
        STD_STACK_RET_SEL,
        get_player[out](),
        get_objective[out]()
    )

    STD_RET = out


def while_test():
    a: Score = 1

    while a < 1048577:
        # "say While Iteration!"
        print_var["a", a]()
        a *= 2
        # print["a2 = ", a]()

    log["while_test", "Done!"]()


def while_test2():
    i: Score
    j: Score

    i = 0
    while i < 5:
        j = 0
        while j < 5:
            print[{"color": "light_purple"}, "i", {"color": "gray"}, " = ", {"color": "gold"}, i, {
                "color": "gray"}, ", ", {"color": "light_purple"}, "j", {"color": "gray"}, " = ", {
                "color": "gold"}, j]()
            j += 1
        i += 1


def while_test3():
    # TODO: Currently broken
    print["[0]"]()

    while 1:
        print["[1]"]()
        break

    print["[2]"]()

    while 1:
        print["[3]"]()
        while 1:
            print["[4]"]()
            break
        print["[5]"]()
        break

    print["[6]"]()


def sum(a: Score, b: Score):
    # TODO: right arg popping
    # TODO: this comepletely doesn't work
    pop[1]()
    a = STD_RET
    pop[1]()
    b = STD_RET

    print["a = ", a]()
    print["b = ", b]()
    c: Score = a + b
    print["a + b = c = ", c]()
    return c


def sum_test():
    c: Score = sum(1, 2)

    print["c = ", c]()


#
# def fib(n: Score):
#     print["Starting fib with n = ", n]()
#     fib_nm1: Score
#     fib_nm2: Score
#     fib_nm0: Score
#
#     if n == 1:
#         return 1
#     elif n == 2:
#         return 1
#     else:
#         fib_nm1 = fib(n - 1)
#         fib_nm2 = fib(n - 2)
#         fib_nm0 = fib_nm1 + fib_nm2
#         return fib_nm0
#
#
# def fib_test():
#     n: Score = 1
#     fib_n: Score
#
#     while n < 3:
#         fib_n = fib(n)
#
#         print2["fib(", n, ") = ", fib_n]()
#         n += 1


def stack_test():
    STD_RET = 0

    STD_ARG = 42
    print_var["arg", STD_ARG]()
    push[1]()

    STD_ARG = 43
    print_var["arg", STD_ARG]()
    push[1]()

    # stackdump[1]()

    # peek[1]()
    STD_RET = -404
    pop[1]()
    print_var["ret", STD_RET]()

    STD_RET = -404
    pop[1]()
    print_var["ret", STD_RET]()


def main():
    load()

    while_test()
    sum_test()
    fizz_buzz()
    collatz()
    find_score_overflow()
    stack_test()
    stackdump[1]()
    stackdump_test()
    while_test2()
    while_test3()
    primes_test()
    # fib_test()

    # a[1]()


def fizz_buzz():
    i: Score = 1
    div_3: Score
    div_5: Score

    while i <= 100:
        print_var["i", i]()

        div_3 = i % 3 == 0
        div_5 = i % 5 == 0

        if div_3 and div_5:
            log["FB", "FizzBuzz"]()
        elif div_3:
            log["FB", "Fizz"]()
        elif div_5:
            log["FB", "Buzz"]()

        i += 1


def collatz():
    n: Score = 237894234
    i: Score = 1

    while n != 1:
        print[
            "n", {"color": "gray"}, "[", {"color": "light_purple"}, i, {"color": "gray"}, "]", {"color": None}, " = ", {
                "color": "gold"}, n]()
        if n % 2 == 0:
            n /= 2
        else:
            n *= 3
            n += 1

        # if n == 1:
        #     break

        i += 1


def find_score_overflow():
    a: Score = 1

    while a > 0:
        a *= 2
        print_var["a", a]()

    a -= 1
    print_var["a-1", a]()
    # print["a = ", a]()


def min_stack_i[stack_nr: int]():
    # if stack_nr == 1:
    #     log["min_stack_i", {"color": "red"}, "min_stack_i does not work with stack_nr == 1!"]()
    #     return 0

    # does not work with stack_nr == 1 bc while loops create a stack
    stack_length: Score[tag_of_stack_nr[stack_nr](), STD_STACK_OBJECTIVE]
    stack_length_copy: Score = stack_length
    i: Score = 0
    does_exist: Score

    while i < stack_length:
        # print_var["i", i]()
        exists[stack_nr, i]()

        does_exist = STD_RET

        if does_exist:
            return i

        i += 1


def stackdump[stack_nr]():
    i: Score = min_stack_i[stack_nr]()
    stack_length: Score[tag_of_stack_nr[stack_nr](), STD_STACK_OBJECTIVE]
    does_exist: Score

    stack_length_copy: Score = stack_length

    data_tmp: Nbt[AnyDataType, "storage", "mcutils:temp", "data"]
    all_data: Nbt[AnyDataType, "entity", STD_STACK_RET_SEL, ""]
    data: Nbt[AnyDataType, "storage", "mcutils:temp", "data.data"]
    tags: Nbt[AnyDataType, "storage", "mcutils:temp", "data.Tags"]

    b: Score = stack_length_copy
    b -= i
    b += 1
    print[{"underlined": True}, "Enumerating ", {"color": "gold"}, b, {"color": None}, " elements of stack ", {
        "color": "light_purple"}, stack_nr, {"color": None}, ":"]()

    while i <= stack_length_copy:
        exists[stack_nr, i]()
        does_exist = STD_RET

        peek_any[stack_nr, i]()

        data_tmp = all_data

        if does_exist:
            print[
                {"color": "light_purple"}, "[", i, "]", {"color": "gray"}, ": ",
                {"color": "gold"}, STD_RET,
                {"color": "gray"}, " - ", {"color": None}, data,
                {"color": "gray"}, " ", tags
            ]()
        else:
            print[
                {"color": "light_purple"}, "[", i, "]", {"color": "gray"}, ": ",
                {"color": "gold"}, "missing",
            ]()

        i += 1


def stackdump_test():
    STD_ARG = [1, 2, 3]
    push[2]()
    STD_ARG = "asd"
    push[2]()
    STD_ARG = [.12323423, 5.0]
    push[2]()
    STD_ARG = {"hihi": "huhu", "hello": ["world"]}
    push[2]()

    stackdump[2]()

    pop[2]()
    pop[2]()
    pop[2]()
    pop[2]()


# def primes(below):
#     i = 1
#
#     while i < below:
#         isprime = True
#
#         for x in range(2, i):
#             if i % x == 0:
#                 isprime = False
#                 # break
#
#         if isprime:
#             print(i)
#
#         i += 1

def primes_test():
    below: Score = 50
    i: Score = 1
    isprime: Score
    x: Score

    while i < below:
        isprime = 1

        x = 2
        while x < i:
            if i % x == 0:
                isprime = 0
                # break

            x += 1

        if isprime:
            print["i", {"color": "gray"}, " = ", {"color": "gold"}, i, {"color": None}, " PRIME"]()
        else:
            print["i", {"color": "gray"}, " = ", {"color": "gold"}, i]()

        i += 1
