STD_OBJECTIVE: ScoreboardObjective["mcutils"]

STD_STACK_OBJECTIVE: ScoreboardObjective["stack"]
STD_STACK_INDEX_OBJECTIVE: ScoreboardObjective["index"]
# STD_STACK_VALUE_OBJECTIVE: ScoreboardObjective["value"]
STD_STACK_TAG: Tag["stack"]
STD_STACK_RET_TAG: Tag["stack_ret"]
STD_STACK_RET_SEL = "@e[tag=%s, limit=1]" % (STD_STACK_RET_TAG,)


def print_var[name, var]():
    print[name, {"color": "gray"}, " = ", {"color": "gold"}, var]()


def gamerule[rule, value]():
    "gamerule %s %s" % (rule, value)


def gamerule_max_command_chain_length[value]():
    log["mcutils", "Set maxCommandChainLength to ", {"color": "gold"}, value, {"color": None}, "."]()
    gamerule["maxCommandChainLength", value]()


def set_max_command_chain_length():
    gamerule_max_command_chain_length["2147483647"]()


def scoreboard_add_objective[name]():
    "scoreboard objectives add %s dummy" % (name,)


def load():
    scoreboard_add_objective[STD_STACK_INDEX_OBJECTIVE]()
    # scoreboard_add_objective[STD_STACK_VALUE_OBJECTIVE]()
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


def while_test():
    i: Int = 1

    while i < 5:
        print_var["i", i]()
        i += 1
        print_var["i + 1", i]()

    log["while_test", "Done!"]()


def while_test2():
    i: Int
    j: Int

    i = 0
    while i < 5:
        j = 0
        while j < 5:
            print[
                {"color": "light_purple"}, "i", {"color": "gray"}, " = ", {"color": "gold"}, i,
                {"color": "gray"}, ", ", {"color": "light_purple"}, "j", {"color": "gray"}, " = ", {
                    "color": "gold"}, j
            ]()
            j += 1
        i += 1


def while_test3():
    print["[0]"]()

    while 1:
        print["[1]"]()
        break
        print["[2] !!"]()

    print["[2]"]()

    while 1:
        print["[3]"]()
        break
        print["[4] !!"]()

    print["[4]"]()

    while 1:
        print["[5]"]()
        while 1:
            print["[6]"]()
            break
            print["[7] !!"]()
        print["[7]"]()
        break
        print["[8] !!"]()

    print["[8]"]()

    while 1:
        print["[9]"]()
        while 1:
            print["[10]"]()
            while 1:
                print["[11]"]()
                break
                print["[12] !!"]()
            break
            print["[12] !!"]()
        print["[12]"]()
        break
        print["[14] !!"]()

    print["[13]"]()

    while 1:
        print["[14]"]()

        while 1:
            print["[15]"]()
            if 1:
                print["[16]"]()
                break
                print["[17] !!"]()

            print["[17] !!"]()

        print["[17]"]()

        if 1:
            print["[18]"]()
            break
            print["[19] !!"]()

        print["[19] !!"]()

    print["[19]"]()


# def _while_test4(a):
#     log["_while_test4", "[", a, "] Called!"]()
#     if a <= 0:
#         log["_while_test4", "[", a, "] Returning!"]()
#         return
#
#     a_minus_1: Score
#     log["_while_test4", "[", a, "] Starting loop!"]()
#
#     i: Score = 0
#
#     while i < 1:
#         log["_while_test4", "[", a, "] i = ", {"color": "gold"}, i]()
#
#         STD_ARG = i
#         push[1]()
#         STD_ARG = a
#         push[1]()
#         a_minus_1 = a
#         a_minus_1 -= 1
#         log["_while_test4", "[", a, "] Calling _while_test4(", a_minus_1, ")!"]()
#         _while_test4(a_minus_1)
#         pop[1]()
#         a = STD_RET
#         log["_while_test4", "[", a, "] Returned from _while_test4(", a_minus_1, ")!"]()
#         pop[1]()
#         i = STD_RET
#
#         log["_while_test4", "[", a, "] i = ", i, " after pop"]()
#         i += 1
#         log["_while_test4", "[", a, "] i = ", i, " after increment, next iter!"]()
#
#
# def while_test4():
#     _while_test4(2)


def _early_return_test():
    i: Int = 0

    while i < 5:
        print_var["i", i]()
        i += 1

        if i == 3:
            log["_early_return_test", "Returning early!"]()
            return

            log["_early_return_test", "You should not see this! (1)"]()

    log["_early_return_test", "You should not see this! (2)"]()


def early_return_test():
    log["early_return_test", "Starting!"]()
    _early_return_test()
    log["early_return_test", "Done!"]()


def sum(a: Int, b: Int):
    print["a = ", a]()
    print["b = ", b]()
    c: Score = a + b
    print["a + b = c = ", c]()
    return c


def sum_test():
    c = sum(1, 2)
    print["c = ", c]()

    c = sum(2, -3)
    print["c = ", c]()

    c = sum(52, 56)
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


def stack_test[stack_nr]():
    print_var["push", 42]()
    push[stack_nr](42)

    print_var["push", 43]()
    push[stack_nr](43)

    # stackdump[stack_nr]()

    peek_val = peek[stack_nr]()
    print_var["peek", peek_val]()

    ret = pop[stack_nr]()
    print_var["ret", ret]()

    ret = pop[stack_nr]()
    print_var["ret", ret]()


def main():
    load()

    while_test()
    sum_test()
    fizz_buzz()
    collatz()
    find_score_overflow()
    stack_test[1]()
    stack_test[2]()
    stackdump[1]()
    stackdump_test()
    while_test2()
    while_test3()
    # while_test4()
    primes_test()
    nbt_test()
    early_return_test()
    fact_test()
    # fib_test()

    # a[1]()


def fizz_buzz():
    i: Int = 1

    while i <= 100:
        print_var["i", i]()

        if i % 15 == 0:
            log["FB", "FizzBuzz"]()
        elif i % 3 == 0:
            log["FB", "Fizz"]()
        elif i % 5 == 0:
            log["FB", "Buzz"]()

        i += 1


def collatz():
    n: Int = 237894234
    i: Int = 1

    while n != 1:
        print[
            "n", {"color": "gray"}, "[", {"color": "light_purple"}, i, {"color": "gray"}, "]",
            {"color": None}, " = ", {"color": "gold"}, n
        ]()
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
    # does not work with stack_nr == 1 bc while loops create a stack
    # update: does kinda work idk y
    # if stack_nr == 1:
    #     log["min_stack_i", {"color": "red"}, "min_stack_i does not work with stack_nr == 1!"]()
    #     return 0

    stack_length_copy: Int = Score[tag_of_stack_nr[stack_nr](), STD_STACK_OBJECTIVE]
    i: Score = 0

    while i < stack_length_copy:
        # print_var["i", i]()

        if exists[stack_nr, i]():
            # log["min_stack_i", "Returning ", {"color": "gold"}, i, {"color": None}, "."]()
            return i

        i += 1


def stackdump[stack_nr]():
    i: Int = min_stack_i[stack_nr]()
    # print_var["min_stack_i", i]()

    stack_length: Score[tag_of_stack_nr[stack_nr](), STD_STACK_OBJECTIVE]
    num_elements: Int = stack_length - i + 1
    # print_var["stack_length", stack_length_copy]()

    print[
        {"underlined": True}, "Enumerating ",
        {"color": "gold"}, num_elements,
        {"color": None}, " elements of stack ",
        {"color": "light_purple"}, stack_nr,
        {"color": None}, " starting with ",
        {"color": "gray"}, "[", {"color": "light_purple"}, i, {"color": "gray"}, "]",
        {"color": None}, ":"
    ]()

    set_max_command_chain_length()

    while i <= stack_length:
        val = peek_any[stack_nr, i]()

        if exists[stack_nr, i]():
            print[
                {"color": "gray"}, "[", {"color": "light_purple"}, i, {"color": "gray"}, "]", {"color": "gray"}, " = ",
                {"color": "gold"}, val,
                # {"color": "gray"}, " - ", data,
                # " - ", tags
            ]()
        else:
            print[
                {"color": "gray"}, "[", {"color": "light_purple"}, i, {"color": "gray"}, "]", {"color": "gray"}, " = ",
                {"color": "red"}, "missing!",
            ]()

        i += 1

    gamerule_max_command_chain_length["65536"]()


def stackdump_test():
    stack_length: Score[tag_of_stack_nr[2](), STD_STACK_OBJECTIVE]

    push[2]([1, 2, 3])
    push[2]("asd")
    push[2]("you should never see this")
    a: Score = stack_length
    push[2]([.12323423, 5.0])
    push[2]({"hihi": "huhu", "hello": ["world"]})

    _pop_any[2, a]()

    stackdump[2]()

    pop[2]()
    pop[2]()
    pop[2]()
    pop[2]()
    pop[2]()


def primes_test():
    i: Int = 2

    while i < 100:
        isprime: Int = 1

        x: Int = 2
        while x < i:
            if i % x == 0:
                isprime = 0
                break

            x += 1

        if isprime:
            print["i", {"color": "gray"}, " = ", {"color": "gold"}, i, {"color": None}, " PRIME"]()
        else:
            # print["i", {"color": "gray"}, " = ", {"color": "gold"}, i]()
            pass
        i += 1


def nbt_test():
    a: String = "🏳️‍🌈"
    print_var["a", a]()

    a_len: Int = a
    print_var["len(a)", a_len]()

    a_double: Double = 0.5
    print_var["a", a_double]()
    a_double += 1
    print_var["a+1", a_double]()

    a_float: Float = 0.5
    print_var["a", a_float]()
    a_float += 1
    print_var["a+1", a_float]()

    a_int: Int[Nbt] = 42
    print_var["a", a_int]()
    a_int += 1
    print_var["a+1", a_int]()

    b: Compound = {"a": 1, "b": 2}
    print_var["a", b]()
    a_len = b
    print_var["len(a)", a_len]()


def fact(num: Int):
    a: Int = num
    # log["fact", "a = ", {"color": "gold"}, a, {"color": None}, "."]()

    if a > 10:
        # log["fact", "a > 10, returning -1!"]()
        return -1

    if a == 0:
        # log["fact", "a == 0, returning 1!"]()
        return 1

    out: Int = 1
    i: Int = 1

    while i <= a:
        # print_var["out", out]()
        # print_var["i", i]()
        out *= i
        i += 1
        # print_var["out*i", out]()
        # print_var["i+1", i]()

    return out


def fact_test():
    x: Int = 0
    while x <= 11:
        out = fact(x)
        print[{"color": "gray"}, "fact(", {"color": "light_purple"}, x, {"color": "gray"}, ") = ", {
            "color": "gold"}, out]()
        x += 1
