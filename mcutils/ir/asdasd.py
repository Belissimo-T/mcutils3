import dataclasses

from mcutils import stores


@dataclasses.dataclass
class Scope:
    symbols: dict[str, stores.ReadableStore]