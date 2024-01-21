import pathlib

from mcutils.ir.statements import *


def main():
    a = Namespace.from_py_ast(ast.parse(pathlib.Path("testprog/simple.py").read_text()))
    breakpoint()


if __name__ == '__main__':
    main()
