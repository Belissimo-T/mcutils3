from ...data import stores
from ...strings import UniqueTag, LiteralString


class Library:
    __pyfuncs__ = "tag_of_stack_nr", "get_player", "get_objective"

    def __init__(self):
        self.std_stack_tags = {}

    def tag_of_stack_nr(self, stack_nr: int) -> UniqueTag:
        if stack_nr not in self.std_stack_tags:
            self.std_stack_tags[stack_nr] = UniqueTag(LiteralString(f"stack{stack_nr}"))

        return self.std_stack_tags[stack_nr]

    def get_player(self, var):
        # breakpoint()
        return var.player

    def get_objective(self, var):
        # breakpoint()
        return var.objective
