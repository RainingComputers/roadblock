import dataclasses
from typing import Self


@dataclasses.dataclass
class Dim:
    x: int
    y: int

    def __repr__(self) -> str:
        return f"x={self.x} y={self.y}"

    def __add__(self, other: Self) -> Self:
        return Dim(self.x + other.x, self.y + other.y)  # type: ignore

    def __mul__(self, other: Self) -> Self:
        return Dim(self.x * other.x, self.y * other.y)  # type: ignore

    def __floordiv__(self, other: Self) -> Self:
        return Dim(self.x // other.x, self.y // other.y)  # type: ignore
