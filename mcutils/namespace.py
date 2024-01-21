import dataclasses


@dataclasses.dataclass
class Location:
    namespace: str
    path: tuple[str, ...]


