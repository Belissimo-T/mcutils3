import typing

T = typing.TypeVar("T")


class GenericMetaclass(type):

    def __init__(cls, name: str, bases: tuple[type, ...], namespace: dict[str, object]):
        super().__init__(name, bases, namespace)

    def __getitem__(self: T, item) -> T:
        # self = the generic class that wants to be subscripted
        if not isinstance(item, tuple):
            item = item,

        # return a new class with the given generic arguments saved and a subclass of self
        return type(self.__name__, (self,), {"__generic_args__": item, "__base_class__": self})

    def __repr__(self: typing.Type["Generic"]):
        if self.__base_class__ is None:
            base_class = self
        else:
            base_class = self.__base_class__

        return f"{base_class.__name__}[{', '.join(map(repr, self.__generic_args__))}]"


class Generic(metaclass=GenericMetaclass):
    __generic_args__: tuple[type, ...] = ()
    __base_class__: type = None


def main():
    class Variable(Generic):
        def __init__(self, name: str):
            self.name = name

        def hello(self):
            print(f"Hello {self.name}!")

    type1 = Variable[int]
    type2 = Variable[str]

    print(dir(type1))

    print(type1, type2)

    var1 = type1("Bob")

    var1.hello()


if __name__ == "__main__":
    main()
