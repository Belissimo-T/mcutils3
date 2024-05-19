from ...data import stores
from ...strings import UniqueTag, LiteralString


class Library:
    __pyfuncs__ = "tag_of_stack_nr",

    def __init__(self):
        self.std_stack_tags = {}

    def tag_of_stack_nr(self, stack_nr: int) -> UniqueTag:
        if stack_nr not in self.std_stack_tags:
            self.std_stack_tags[stack_nr] = UniqueTag(LiteralString(f"stack{stack_nr}"))

        return self.std_stack_tags[stack_nr]

