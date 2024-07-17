from ..mcutils.lib.std import *
import asd


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


def find_score_overflow():
    a: Score = 1

    b: Long
    c: Double
    c2: Float
    d: Long

    while a > 0:
        a *= 2
        print_var["a", a]()

        b = a
        print_var["b", b]()

        c = b
        print_var["c", c]()

        c2 = b
        print_var["C", c2]()

        d = c
        print_var["d", d]()

        print[""]()

    a -= 1
    print_var["a-1", a]()
    # print["a = ", a]()

    return a


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

    max_int: Long = 2_147_483_647
    print_var["max_int", max_int]()
    max_int += 1
    print_var["max_int+1", max_int]()
