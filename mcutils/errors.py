class CompilationError(Exception):
    pass


def compile_assert(cond: bool, msg: str):
    if not cond:
        raise CompilationError(msg)
