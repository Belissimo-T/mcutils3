STD_OBJECTIVE: ScoreboardObjective["mcutils"]

STD_ARG: Nbt[AnyDataType, "storage", "mcutils:std", "arg"]
STD_RET: Nbt[AnyDataType, "storage", "mcutils:std", "ret"]
# STD_ARG: Score["arg", STD_OBJECTIVE]
# STD_RET: Score["ret", STD_OBJECTIVE]

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


def push[stack_nr]():
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
        print_var["a", a]()
        a *= 2

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


def _early_return_test():
    i: Score = 0

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


def sum(a: Score, b: Score):
    print["a = ", a]()
    print["b = ", b]()
    c: Score = a + b
    print["a + b = c = ", c]()
    return c


def sum_test():
    c: Score = sum(1, 2)
    print["c = ", c]()

    c: Score = sum(2, -3)
    print["c = ", c]()

    c: Score = sum(52, 56)
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
    nbt_test()
    early_return_test()
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
    # does not work with stack_nr == 1 bc while loops create a stack
    # update: does kinda work idk y
    # if stack_nr == 1:
    #     log["min_stack_i", {"color": "red"}, "min_stack_i does not work with stack_nr == 1!"]()
    #     return 0

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
    print[
        {"underlined": True}, "Enumerating ",
        {"color": "gold"}, b,
        {"color": None}, " elements of stack ",
        {"color": "light_purple"}, stack_nr,
        {"color": None}, " starting with ",
        {"color": "gray"}, "[", {"color": "light_purple"}, i, {"color": "gray"}, "]",
        {"color": None}, ":"
    ]()

    set_max_command_chain_length()

    while i <= stack_length_copy:
        exists[stack_nr, i]()
        does_exist = STD_RET

        peek_any[stack_nr, i]()

        data_tmp = all_data

        if does_exist:
            print[
                {"color": "gray"}, "[", {"color": "light_purple"}, i, {"color": "gray"}, "]", {"color": "gray"}, " = ",
                {"color": "gold"}, STD_RET,
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

    STD_ARG = [1, 2, 3]
    push[2]()
    STD_ARG = "asd"
    push[2]()
    a: Score = stack_length
    push[2]()
    STD_ARG = [.12323423, 5.0]
    push[2]()
    STD_ARG = {"hihi": "huhu", "hello": ["world"]}
    push[2]()

    _pop_any[2, a]()

    stackdump[2]()

    pop[2]()
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
    below: Score = 25
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


def nbt_test():
    my_list: Nbt[ListType, "storage", "mcutils:temp", "my_list"] = "🏳️‍🌈"

    print_var["my_list", my_list]()

    my_list_len: Nbt[IntType, "storage", "mcutils:temp", "my_list_len"] = my_list

    print_var["len(my_list)", my_list_len]()
