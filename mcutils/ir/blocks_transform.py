import copy

from . import blocks


def transform_whiles(mcfunctions: dict[tuple[str, ...], blocks.Block]) -> dict[tuple[str, ...], blocks.Block]:
    new_mcfunctions: dict[tuple[str, ...], blocks.Block] = {}

    for mcfunction_name, mcfunction in mcfunctions.items():
        mcfunction_children: dict[tuple[str, ...], blocks.Block] = {}

        current_child_i = 0
        current_child = blocks.Block([], mcfunction.continuation_info)

        for statement in mcfunction.statements:
            if isinstance(statement, blocks.WhileStatement):
                current_child.continuation_info = mcfunction.continuation_info.with_(
                    default=(*mcfunction_name, "while_check_condition")
                )

                mcfunction_children |= {
                    (f"{current_child_i}",): current_child
                }
                current_child_i += 1
                current_child = blocks.Block([], mcfunction.continuation_info)

                in_loop_continuation_info = mcfunction.continuation_info.with_(
                    default=(*mcfunction_name, "while_check_condition"),
                    new_loops=[
                        blocks.LoopContinuationInfo(
                            continue_=(*mcfunction_name, "while_check_condition"),
                            break_=(*mcfunction_name, f"{current_child_i}")
                        )
                    ]
                )

                mcfunctions[statement.body].continuation_info = in_loop_continuation_info
                mcfunction_children.update({
                    ("while", ): mcfunctions[statement.body],
                    ("while_check_condition", ): blocks.Block(
                        # although break/continue in the loop condition check is a bit weird
                        continuation_info=in_loop_continuation_info,
                        statements=[
                            blocks.IfStatement(
                                condition=statement.condition,
                                true_block=(*mcfunction_name, "while"),
                                false_block=in_loop_continuation_info.loops[-1].break_
                            )
                        ]
                    )
                })
            else:
                current_child.statements.append(statement)

        mcfunction_children |= {
            (f"{current_child_i}", ): current_child
        }

        new_mcfunctions |= {(*mcfunction_name, *key): value for key, value in mcfunction_children.items()
                            if key != ("0", )}
        new_mcfunctions |= {mcfunction_name: mcfunction_children["0", ]}

    return new_mcfunctions


def transform_conditionals(mcfunctions: dict[tuple[str, ...], blocks.Block]) -> dict[tuple[str, ...], blocks.Block]:
    """Transform conditionals such that they only occur at most once per mcfunction at the end."""
    new_mcfunctions: dict[tuple[str, ...], blocks.Block] = {}

    for mcfunction_name, mcfunction in mcfunctions.items():
        mcfunction_children: dict[tuple[str, ...], blocks.Block] = {}

        current_child_i = 0
        current_child = blocks.Block([], mcfunction.continuation_info)

        for node in mcfunction.statements:
            node = copy.deepcopy(node)

            current_child.statements.append(node)

            if isinstance(node, blocks.IfStatement):
                mcfunction_children |= {
                    (f"{current_child_i}", ): current_child
                }
                current_child_i += 1
                current_child.continuation_info.default = None  # this mcfunction ends here

                mcfunctions[node.true_block].continuation_info.default = (*mcfunction_name, f"{current_child_i}")
                if node.true_block is not None:
                    mcfunctions[node.false_block].continuation_info.default = (*mcfunction_name, f"{current_child_i}")
                else:
                    node.false_block = (*mcfunction_name, f"{current_child_i}")

                current_child = blocks.Block([], mcfunction.continuation_info)

        mcfunction_children |= {
            (f"{current_child_i}", ): current_child
        }
        new_mcfunctions |= {(*mcfunction_name, *key): value for key, value in mcfunction_children.items()
                            if key != ("0", )}
        new_mcfunctions |= {mcfunction_name: mcfunction_children["0", ]}

    return new_mcfunctions


def transform_all(sequences: dict[tuple[str, ...], blocks.Block]) -> dict[tuple[str, ...], blocks.Block]:
    # transform whiles
    sequences = transform_whiles(sequences)

    # transform ifs
    sequences = transform_conditionals(sequences)

    # remove stopping statements
    # sequences = remove_stopping_statements(sequences)

    return sequences
