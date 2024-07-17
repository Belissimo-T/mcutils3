import ast_comments as ast
import pathlib

import mcutils.lib.std
from mcutils import strings
from mcutils.ir import tree, commands, datapack, blocks


def load_file(path: tuple[str, ...]):
    fs_path = pathlib.Path(*path)

    py_lib_path = fs_path.with_suffix(".py")
    mc_py_path = fs_path.with_suffix(".mc.py")

    try:
        py_lib_code = compile(py_lib_path.read_text("utf-8"), py_lib_path, "exec")
    except FileNotFoundError:
        py_lib = None
    else:
        locals_dict = {}
        exec(py_lib_code, locals_dict)

        py_lib = locals_dict["Library"]

    mc_py_ast = ast.parse(mc_py_path.read_text("utf-8"))

    return tree.File.from_py_ast(
        mc_py_ast,
        py_library=py_lib,
        path=path
    )


def main():
    std_path = ("std",)

    stack = []

    b = commands.CompileNamespace.from_tree_namespace(a)

    std_lib = mcutils.lib.std.Library()
    std_file = mcutils.ir.tree.File.from_py_ast(
        ast.parse(pathlib.Path(mcutils.lib.std.__file__).with_suffix(".mc.py").read_text("utf-8")),
        py_library=std_lib,
        path=std_path
    )

    std_lib_config = blocks.StdLibConfig(
        stack_push=(std_path + ("push",), (1,)),
        stack_pop=(std_path + ("pop",), (1,)),
        stack_peek=(std_path + ("peek",), (1,)),
    )

    b.resolve_templates(
        [path for path, func in b.function_templates.items() if len(func.get_compile_time_args()) == 0],
        std_lib_config
    )

    d = datapack.Datapack("test", {"test": b})
    d.export(pathlib.Path("testout").absolute())

    print(strings._ID)


if __name__ == '__main__':
    main()
