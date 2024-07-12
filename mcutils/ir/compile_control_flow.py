from __future__ import annotations

import copy

from . import blocks, tree, tree_statements_base
from ..errors import compile_assert


def transform_whiles(mcfunctions: dict[tuple[str, ...], blocks.Block]) -> dict[tuple[str, ...], blocks.Block]:
    new_mcfunctions: dict[tuple[str, ...], blocks.Block] = {}

    for mcfunction_name, mcfunction in mcfunctions.items():
        mcfunction_children: dict[tuple[str, ...], blocks.Block] = {}

        current_child_i = 0
        current_child = blocks.Block([], copy.copy(mcfunction.continuation_info))

        for statement in mcfunction.statements:
            if isinstance(statement, blocks.WhileStatement):
                while_chk_cond_func_name = f"__while_chk_cond{current_child_i}"

                current_child.continuation_info = mcfunction.continuation_info.with_(
                    default=(*mcfunction_name, while_chk_cond_func_name)
                )

                mcfunction_children |= {
                    (f"{current_child_i}",): current_child
                }
                current_child_i += 1
                current_child = blocks.Block([], mcfunction.continuation_info)

                in_loop_continuation_info = mcfunction.continuation_info.with_(
                    default=(*mcfunction_name, while_chk_cond_func_name),
                    new_loops=[
                        blocks.LoopContinuationInfo(
                            continue_=(*mcfunction_name, while_chk_cond_func_name),
                            break_=(*mcfunction_name, f"{current_child_i}")
                        )
                    ]
                )

                mcfunctions[statement.body].continuation_info = in_loop_continuation_info

                mcfunction_children.update({
                    (while_chk_cond_func_name,): blocks.Block(
                        # although break/continue in the loop condition check is a bit weird
                        continuation_info=in_loop_continuation_info,
                        statements=[
                            blocks.IfStatement(
                                condition=statement.condition,
                                true_block=statement.body,
                                false_block=in_loop_continuation_info.loops[-1].break_,
                                no_redirect_branches=True
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

                if node.no_redirect_branches:
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
            if isinstance(statement, tree_statements_base.StoppingStatement):
                if isinstance(statement, tree_statements_base.ContinueStatement):
                    mcfunction_name_copy = list(mcfunction_name)
                    # TODO: remove this icky code
                    while mcfunction_name_copy:
                        try:
                            if mcfunctions[tuple(mcfunction_name_copy)].continuation_info.loops:
                                break
                        except KeyError:
                            pass
                        mcfunction_name_copy.pop()
                    else:
                        compile_assert(False)

                    statements.append(blocks.BlockCallStatement(mcfunctions[tuple(mcfunction_name_copy)].continuation_info.loops[-1].continue_))
                elif isinstance(statement, tree_statements_base.BreakStatement):
                    mcfunction_name_copy = list(mcfunction_name)
                    while mcfunction_name_copy:
                        try:
                            if mcfunctions[tuple(mcfunction_name_copy)].continuation_info.loops:
                                break
                        except KeyError:
                            pass

                        mcfunction_name_copy.pop()
                    else:
                        compile_assert(False)

                    statements.append(blocks.BlockCallStatement(
                        mcfunctions[tuple(mcfunction_name_copy)].continuation_info.loops[-1].break_))
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
