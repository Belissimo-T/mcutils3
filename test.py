import ast
import pathlib

from mcutils.ir import tree, blocks, compile_control_flow, commands, datapack


def main():
    from mcutils.lib.std2 import stack

    py_lib = stack.Library()

    a = tree.File.from_py_ast(
        ast.parse(pathlib.Path("mcutils/lib/std2/stack.mc.py").read_text()),
        py_library=py_lib
    )

    a.resolve_templates(["main"])

    b = blocks.Namespace2.from_tree_namespace(a)

    c = commands.Namespace3.from_namespace2(b)
    d = datapack.Datapack("test", {"test": c})
    d.export(pathlib.Path("testout").absolute())


if __name__ == '__main__':
    main()
