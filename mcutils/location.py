import dataclasses


@dataclasses.dataclass
class Location:
    namespace: str
    path: tuple[str, ...]

    def to_str(self):
        return f"{self.namespace}:{'/'.join(self.path)}"

    def __str__(self):
        return self.to_str()
