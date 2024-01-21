import ast
import pathlib

from mcutils.ir import tree, blocks, blocks_transform


def main():
    a = tree.Namespace.from_py_ast(ast.parse(pathlib.Path("testprog/simple.py").read_text()))
    b = blocks.Namespace2.from_tree_namespace(a)
    for func in b.functions.values():
        func.blocks = blocks_transform.transform_all(func.blocks)
    breakpoint()


if __name__ == '__main__':
    main()
