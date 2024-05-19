from mcutils import strings
from mcutils.data import stores


def get_temp_var(name: str) -> stores.ScoreboardStore:
    return stores.ScoreboardStore(strings.UniqueScoreboardPlayer(strings.LiteralString(name)), strings.UniqueScoreboardObjective(strings.LiteralString("mcutils")))
