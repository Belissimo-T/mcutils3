# class List(std.object.object):
#     def __init__(self: Int):
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
    x = Score = 1

    # local scope
    x = List()  # x is int object id
    x = 1  # x is int 1
    x = 1  # x is int 1
    x = [1]  # x is nbt list
    x = "asd"  # x is nbt str

    # def func2():
    #     print["x is ", x, "for me"]()


class MyTestClass:
    def __init__(self, init_arg):
        ...

def datatypes():
    # Means Of Storage
    # - Score
    a: Score[player, objective]
    # - Nbt
    a: StorageData[name, path]
    a: EntityData[selector, path]
    a: BlockData[location, path]
    # - LocalScope
    a: LocalScope[name]

    # Types
    a: Any

    a: Number

    a: WholeNumber
    a: Byte
    a: Short
    a: Int
    a: Long

    a: RealNumber
    a: Double
    a: Float

    a: String
    a: List
    a: Compound
