from .. import strings
from ..data import stores


MCUTILS_STD_OBJECTIVE = strings.UniqueScoreboardObjective(strings.LiteralString("mcutils_std"))


def get_temp_var(name: str) -> stores.ScoreboardStore:
    return stores.ScoreboardStore(strings.UniqueScoreboardPlayer(strings.LiteralString(name)), MCUTILS_STD_OBJECTIVE)
