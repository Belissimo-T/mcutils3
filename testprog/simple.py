def fizz_buzz():
    i: Nbt[IntType] = 1

    while i <= 100:
        div_3 = i % 3 == 0
        div_5 = i % 5 == 0

        if div_3 and div_5:
            print("FizzBuzz")
        elif div_3:
            print("Fizz")
        elif div_5:
            print("Buzz")

        i = i + 1


def fib(n: Score):
    if n <= 1:
        return 1

    return fib(n - 1) + fib(n - 2)