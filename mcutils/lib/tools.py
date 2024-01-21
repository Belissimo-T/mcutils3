import ast

from ..ir import commands


def std_print(node: ast.expr) -> commands.McFunction:
    breakpoint()

    func = commands.McFunction([
            ...
    ])

    return func
