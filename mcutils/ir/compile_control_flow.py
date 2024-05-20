from __future__ import annotations

import copy

from . import blocks, tree
from ..errors import compile_assert


def transform_whiles(mcfunctions: dict[tuple[str, ...], blocks.Block]) -> dict[tuple[str, ...], blocks.Block]:
    new_mcfunctions: dict[tuple[str, ...], blocks.Block] = {}

    for mcfunction_name, mcfunction in mcfunctions.items():
        mcfunction_children: dict[tuple[str, ...], blocks.Block] = {}

        current_child_i = 0
        current_child = blocks.Block([], copy.copy(mcfunction.continuation_info))

        for statement in mcfunction.statements:
            if isinstance(statement, blocks.WhileStatement):
                current_child.continuation_info = mcfunction.continuation_info.with_(
                    default=(*mcfunction_name, "__while_chk_cond")
                )

                mcfunction_children |= {
                    (f"{current_child_i}",): current_child
                }
                current_child_i += 1
                current_child = blocks.Block([], mcfunction.continuation_info)

                in_loop_continuation_info = mcfunction.continuation_info.with_(
                    default=(*mcfunction_name, "__while_chk_cond"),
                    new_loops=[
                        blocks.LoopContinuationInfo(
                            continue_=(*mcfunction_name, "__while_chk_cond"),
                            break_=(*mcfunction_name, f"{current_child_i}")
                        )
                    ]
                )

                mcfunctions[statement.body].continuation_info = in_loop_continuation_info
                mcfunction_children.update({
                    ("__while_chk_cond",): blocks.Block(
                        # although break/continue in the loop condition check is a bit weird
                        continuation_info=in_loop_continuation_info,
                        statements=[
                            blocks.IfStatement(
                                condition=statement.condition,
                                true_block=statement.body,
                                false_block=in_loop_continuation_info.loops[-1].break_,
                                force_no_redirect_branches=True
                            )
                        ]
                    )
                })
            else:
                current_child.statements.append(statement)

        mcfunction_children |= {
            (f"{current_child_i}",): current_child
        }

        new_mcfunctions |= {(*mcfunction_name, *key): value for key, value in mcfunction_children.items()
                            if key != ("0",)}
        new_mcfunctions |= {mcfunction_name: mcfunction_children["0",]}

    return new_mcfunctions


def transform_conditionals(mcfunctions: dict[tuple[str, ...], blocks.Block]) -> dict[tuple[str, ...], blocks.Block]:
    """Transform conditionals such that they only occur at most once per mcfunction at the end."""
    new_mcfunctions: dict[tuple[str, ...], blocks.Block] = {}

    for mcfunction_name, mcfunction in mcfunctions.items():
        mcfunction_children: dict[tuple[str, ...], blocks.Block] = {}

        current_child_i = 0
        current_child = blocks.Block([], copy.copy(mcfunction.continuation_info))

        for node in mcfunction.statements:
            node = copy.deepcopy(node)

            current_child.statements.append(node)

            if isinstance(node, blocks.IfStatement):
                mcfunction_children |= {
                    (f"{current_child_i}",): current_child
                }
                current_child_i += 1
                current_child.continuation_info.default = None  # this mcfunction ends here

                if node.force_no_redirect_branches:
                    pass
                else:
                    mcfunctions[node.true_block].continuation_info = (
                        mcfunctions[node.true_block].continuation_info.with_(
                            default=(*mcfunction_name, f"{current_child_i}")
                        )
                    )
                    if node.false_block is not None:
                        mcfunctions[node.false_block].continuation_info = (
                            mcfunctions[node.false_block].continuation_info.with_(
                                default=(*mcfunction_name, f"{current_child_i}")
                            )
                        )
                    else:
                        node.false_block = (*mcfunction_name, f"{current_child_i}")

                current_child = blocks.Block([], mcfunction.continuation_info)

        # if len(mcfunction_children) == 1:
        #     breakpoint()

        mcfunction_children |= {
            (f"{current_child_i}",): current_child
        }
        new_mcfunctions |= {(*mcfunction_name, *key): value for key, value in mcfunction_children.items()
                            if key != ("0",)}
        new_mcfunctions |= {mcfunction_name: mcfunction_children["0",]}

    return new_mcfunctions


def remove_stopping_statements(mcfunctions: dict[tuple[str, ...], blocks.Block]) -> dict[tuple[str, ...], blocks.Block]:
    out = {}

    for mcfunction_name, mcfunction in mcfunctions.items():
        statements = []
        for statement in mcfunction.statements:
            if isinstance(statement, tree.StoppingStatement):
                if isinstance(statement, tree.ContinueStatement):
                    statements.append(blocks.BlockCallStatement(mcfunction.continuation_info.loops[0].continue_))
                elif isinstance(statement, tree.BreakStatement):
                    statements.append(blocks.BlockCallStatement(mcfunction.continuation_info.loops[0].break_))
                elif isinstance(statement, tree.ReturnStatement):
                    statements.append(statement)
                    statements.append(blocks.BlockCallStatement(mcfunction.continuation_info.return_))
                elif isinstance(statement, blocks.IfStatement):
                    statements.append(statement)
                else:
                    compile_assert(False)

                break
            else:
                statements.append(statement)
        else:
            statements.append(blocks.BlockCallStatement(mcfunction.continuation_info.default))

        statements = [s for s in statements if not (isinstance(s, blocks.BlockCallStatement) and s.block is None)]

        out[mcfunction_name] = blocks.Block(statements, mcfunction.continuation_info)

    return out


def transform_all(sequences: dict[tuple[str, ...], blocks.Block]) -> dict[tuple[str, ...], blocks.Block]:
    sequences = transform_whiles(sequences)

    sequences = transform_conditionals(sequences)

    sequences = remove_stopping_statements(sequences)

    return sequences
