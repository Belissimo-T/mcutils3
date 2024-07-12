import ast_comments as ast
import pathlib

from mcutils import strings
from mcutils.ir import tree, commands, datapack


def main():
    from mcutils.lib.std2 import stack

    py_lib = stack.Library()

    a = tree.File.from_py_ast(
        ast.parse(pathlib.Path("mcutils/lib/std2/stack.mc.py").read_text("utf-8")),
        py_library=py_lib
    )

    b = commands.CompileNamespace.from_tree_namespace(a)

    std_lib_config = commands.StdLibConfig(
        stack_push=(("push",), (1,)),
        stack_pop=(("pop",), (1,)),
        stack_peek=(("peek",), (1,)),
    )

    b.resolve_templates(["main"], std_lib_config)

    d = datapack.Datapack("test", {"test": b})
    d.export(pathlib.Path("testout").absolute())

    print(strings._ID)


if __name__ == '__main__':
    main()
