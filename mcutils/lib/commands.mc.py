from std import *

def gamerule[rule, value]():
    "gamerule %s %s" % (rule, value)


def gamerule_max_command_chain_length[value]():
    log["mcutils", "Set maxCommandChainLength to ", {"color": "gold"}, value, {"color": None}, "."]()
    gamerule["maxCommandChainLength", value]()


def set_max_command_chain_length():
    gamerule_max_command_chain_length["2147483647"]()


def scoreboard_add_objective[name]():
    "scoreboard objectives add %s dummy" % (name,)

