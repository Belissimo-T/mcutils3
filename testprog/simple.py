def fizz_buzz():
    i = 1
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
