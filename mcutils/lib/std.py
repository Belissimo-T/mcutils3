import typing

from ..data import stores
from ..ir import tree
from .. import tellraw, strings
from ..errors import CompilationError


class Library:
    __pyfuncs__ = "tag_of_stack_nr", "get_player", "get_objective", "print", "log"

    def __init__(self):
        self.std_stack_tags = {}

    def tag_of_stack_nr(self, stack_nr: int) -> strings.UniqueTag:
        if stack_nr not in self.std_stack_tags:
            self.std_stack_tags[stack_nr] = strings.UniqueTag(strings.LiteralString(f"stack{stack_nr}"))

        return self.std_stack_tags[stack_nr]

    def get_player(self, var):
        # breakpoint()
        return var.player

    def get_objective(self, var):
        # breakpoint()
        return var.objective

    def print(self, *args):
        def _print(existing_strings: dict[str, set[str]], resolve_string: typing.Callable[[strings.String], str]):
            out_text_components: list[tellraw.TextComponent] = []

            curr_style = {}

            for arg in args:
                match arg:
                    case dict():
                        curr_style |= {k: tellraw.UNSET if v is None else v for k, v in arg.items()}
                    case str():
                        out_text_components.append(tellraw.PlainText(text=arg, **curr_style))
                    case int():
                        out_text_components.append(tellraw.PlainText(text=str(arg), **curr_style))
                    case float():
                        out_text_components.append(tellraw.PlainText(text=str(arg), **curr_style))
                    case stores.ScoreboardStore(player=player, objective=objective):
                        out_text_components.append(
                            tellraw.ScoreboardValue(player=resolve_string(player), objective=resolve_string(objective),
                                                    **curr_style)
                        )
                    case stores.NbtStore(nbt_container_type=type_, nbt_container_argument=arg, path=path):
                        out_text_components.append(
                            tellraw.NbtValue(
                                path=resolve_string(path),
                                block=resolve_string(arg) if type_ == "block" else tellraw.UNSET,
                                entity=resolve_string(arg) if type_ == "entity" else tellraw.UNSET,
                                storage=resolve_string(arg) if type_ == "storage" else tellraw.UNSET,
                                **curr_style
                            )
                        )
                    case _:
                        raise CompilationError(f"Invalid argument {arg!r}")

            return f"tellraw @a {tellraw.get_raw_json(*out_text_components)}"

        return tree.LiteralStatement([strings.DynamicString(_print)]),

    def log(self, prefix, *args):
        return self.print({"color": "light_purple"}, f"[{prefix}]", {"color": None}, " ", *args)
