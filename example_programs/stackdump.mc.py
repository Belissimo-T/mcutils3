def min_stack_i[stack_nr: int]():
    # does not work with stack_nr == 1 bc while loops create a stack
    # update: does kinda work idk y
    # if stack_nr == 1:
    #     log["min_stack_i", {"color": "red"}, "min_stack_i does not work with stack_nr == 1!"]()
    #     return 0

    stack_length_copy: Int = Score[tag_of_stack_nr[stack_nr](), STD_STACK_OBJECTIVE]
    i: Score = 0

    while i < stack_length_copy:
        # print_var["i", i]()

        if exists[stack_nr, i]():
            # log["min_stack_i", "Returning ", {"color": "gold"}, i, {"color": None}, "."]()
            return i

        i += 1


def stackdump[stack_nr]():
    i: Int = min_stack_i[stack_nr]()
    # print_var["min_stack_i", i]()

    stack_length: Score[tag_of_stack_nr[stack_nr](), STD_STACK_OBJECTIVE]
    num_elements: Int = stack_length - i + 1
    # print_var["stack_length", stack_length_copy]()

    print[
        {"underlined": True}, "Enumerating ",
        {"color": "gold"}, num_elements,
        {"color": None}, " elements of stack ",
        {"color": "light_purple"}, stack_nr,
        {"color": None}, " starting with ",
        {"color": "gray"}, "[", {"color": "light_purple"}, i, {"color": "gray"}, "]",
        {"color": None}, ":"
    ]()

    set_max_command_chain_length()

    while i <= stack_length:
        val = peek_any[stack_nr, i]()

        if exists[stack_nr, i]():
            print[
                {"color": "gray"}, "[", {"color": "light_purple"}, i, {"color": "gray"}, "]", {"color": "gray"}, " = ",
                {"color": "gold"}, val,
                # {"color": "gray"}, " - ", data,
                # " - ", tags
            ]()
        else:
            print[
                {"color": "gray"}, "[", {"color": "light_purple"}, i, {"color": "gray"}, "]", {"color": "gray"}, " = ",
                {"color": "red"}, "missing!",
            ]()

        i += 1

    gamerule_max_command_chain_length["65536"]()

def stackdump_test():
    stack_length: Score[tag_of_stack_nr[2](), STD_STACK_OBJECTIVE]

    push[2]([1, 2, 3])
    push[2]("asd")
    push[2]("you should never see this")
    a: Score = stack_length
    push[2]([.12323423, 5.0])
    push[2]({"hihi": "huhu", "hello": ["world"]})

    _pop_any[2, a]()

    stackdump[2]()

    pop[2]()
    pop[2]()
    pop[2]()
    pop[2]()
    pop[2]()
