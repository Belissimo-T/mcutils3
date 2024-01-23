import ast

from .. import strings
from ..ir import commands


def std_print(node: ast.expr) -> list[strings.String]:
    breakpoint()

    return [
        ...,
    ]


def log(logger: str, *messsage) -> list[strings.String]:
    return [
        strings.LiteralString("say hi! logging!")
    ]
