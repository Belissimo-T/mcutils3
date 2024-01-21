import sys
import traceback
import warnings


class CompilationError(Exception):
    pass


def compile_assert(cond: bool, msg: str = ""):
    if not cond:
        raise CompilationError(msg)


class CompilationWarning(Warning):
    def __init__(self, message: str, traceback_cutoff: int = 1):
        super().__init__(f"{message}")

        self.traceback_cutoff = traceback_cutoff


def issue_warning(warning: str):
    sys.stderr.write("".join(traceback.format_stack()[:-1]))
    warnings.warn(CompilationWarning(warning))
    sys.stderr.write("\n")
