import dataclasses


@dataclasses.dataclass
class Dim:
    x: int
    y: int

    def __repr__(self) -> str:
        return f"x={self.x} y={self.y}"

    def __add__(self, other: "Dim") -> "Dim":
        return Dim(self.x + other.x, self.y + other.y)

    def __mul__(self, other: "Dim") -> "Dim":
        return Dim(self.x * other.x, self.y * other.y)

    def __floordiv__(self, other: "Dim") -> "Dim":
        return Dim(self.x // other.x, self.y // other.y)

    def to_dim3(self) -> "Dim3":
        return Dim3(x=self.x, y=self.y, z=0)


@dataclasses.dataclass
class Dim3:
    x: int
    y: int
    z: int

    def __repr__(self) -> str:
        return f"x={self.x} y={self.y} z={self.z}"

    def __add__(self, other: "Dim3") -> "Dim3":
        return Dim3(self.x + other.x, self.y + other.y, self.z + other.z)

    def __sub__(self, other: "Dim3") -> "Dim3":
        return Dim3(self.x - other.x, self.y - other.y, self.z - other.z)
