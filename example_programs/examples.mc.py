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


def primes():
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
