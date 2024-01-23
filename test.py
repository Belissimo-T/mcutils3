import ast
import pathlib

from mcutils.ir import tree, blocks, blocks_transform, commands, datapack


def main():
    a = tree.Namespace.from_py_ast(ast.parse(pathlib.Path("testprog/simple.py").read_text()))
    b = blocks.Namespace2.from_tree_namespace(a)

    c = commands.Namespace3.from_namespace2(b)
    d = datapack.Datapack("test", {"test": c})
    d.export(pathlib.Path("testout").absolute())


if __name__ == '__main__':
    main()
