import dataclasses

from ..ir import tree_statements_base
from ..data import stores


@dataclasses.dataclass
class ConditionalBlockCallStatement(tree_statements_base.Statement):
    condition: stores.ScoreboardStore
    true_block: tuple[str, ...]
    unless: bool = False


@dataclasses.dataclass
class SimpleAssignmentStatement(tree_statements_base.Statement):
    src: stores.PrimitiveReadableStore
    dst: stores.PrimitiveWritableStore
