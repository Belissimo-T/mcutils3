# class List(std.object.object):
#     def __init__(self: Score):
#         self.data = []  # nbt list
#
#     def __getitem__(self, key):
#         # copy the list
#         # delete n elements from the start
#         # return first element
#         pass


def func1():
    """"""
    # literal command
    "say Hello"

    # unique, for function, but same when recursing
    # can only be int
    x: Score = 1

    # local scope
    x = List()  # x is int object id
    x = 1  # x is int 1
    x: Nbt[Integer] = 1  # x is int 1
    # x = [1]  # x is nbt list
    x = "asd"  # x is nbt str

    def func2():
        print["x is ", x, "for me"]()


class MyTestClass:
    def __init__(self, init_arg):
        ...

def datatypes():
    a: Score = 1

    a: LocalScope[Any] = 1

    a: LocalScope[Number] = 1
    a: LocalScope[WholeNumber] = 1
    a: LocalScope[Byte] = 1
    a: LocalScope[Short] = 1
    a: LocalScope[Int] = 1
    a: LocalScope[Long] = 1
    a: LocalScope[RealNumber] = 1
    a: LocalScope[Double] = 1
    a: LocalScope[Float] = 1

    a: LocalScope[String] = 1
    # a: LocalScope[List[


# if aasd == 2:
#     ...
