from mcutils.ir.statements import *


def main():
    a = Namespace.from_py_ast(ast.parse(open("testprog/simple.py").read()))
    breakpoint()


if __name__ == '__main__':
    main()
