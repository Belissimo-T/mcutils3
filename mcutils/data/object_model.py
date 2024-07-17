from __future__ import annotations

from .. import strings
from ..data import stores


def get_var_of_arg_i(i: int) -> stores.NbtStore:
    return stores.NbtStore("storage", "mcutils:expr_temp", f"func_arg_{i}")


RET_VALUE = stores.NbtStore("storage", "mcutils:expr_temp", "ret_value")
MCUTILS_STD_OBJECTIVE = strings.UniqueScoreboardObjective(strings.LiteralString("mcutils_std"))


def get_temp_var(name: str) -> stores.ScoreboardStore:
    return stores.ScoreboardStore(strings.UniqueScoreboardPlayer(strings.LiteralString(name)), MCUTILS_STD_OBJECTIVE)
