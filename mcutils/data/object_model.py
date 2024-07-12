from __future__ import annotations

from mcutils.data import stores


def get_var_of_arg_i(i: int) -> stores.NbtStore:
    return stores.NbtStore("storage", "mcutils:expr_temp", f"func_arg_{i}")


RET_VALUE = stores.NbtStore("storage", "mcutils:expr_temp", "ret_value")
