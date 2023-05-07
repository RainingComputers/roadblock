import dataclasses


@dataclasses.dataclass
class Dim:
    x: int
    y: int

    def __repr__(self) -> str:
        return f"x={self.x} y={self.y}"
