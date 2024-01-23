from mcutils import strings
from mcutils.data import stores

STD_OBJECTIVE = strings.UniqueScoreboardObjective(strings.LiteralString("mcutils"))
STD_RET = stores.ScoreboardStore(strings.UniqueScoreboardPlayer(strings.LiteralString("ret")), STD_OBJECTIVE)
STD_ARG = stores.ScoreboardStore(strings.UniqueScoreboardPlayer(strings.LiteralString("arg")), STD_OBJECTIVE)
STD_TAG = strings.UniqueTag(strings.LiteralString("mcutils"))
