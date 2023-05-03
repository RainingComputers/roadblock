from random import randrange
import math

import numpy as np

from roadblock.dim import Dim
from roadblock.netlist import MinecraftGate


class MinecraftGrid:
    dim: Dim
    grid: np.ndarray
    gates: list[MinecraftGate]
    out_in_map: dict[int, set[int]]

    def __init__(
        self,
        dim: Dim,
        gates: list[MinecraftGate],
        in_out_map: dict[int, set[int]],
    ):
        self.num_gates = len(gates)

        self.dim = dim
        self.out_in_map = in_out_map
        self.gates = gates

        self.grid = np.full((dim.x, dim.y), -1)
        self.gate_map: list[Dim | None] = [None] * self.num_gates

        self.colors = (
            np.random.randint(50, 256, self.num_gates),
            np.random.randint(50, 256, self.num_gates),
            np.random.randint(50, 256, self.num_gates),
        )

        for gate_id in range(len(gates)):
            self._place(gate_id)

    def _set(self, pos: Dim, dim: Dim, value: int) -> None:
        for y in range(dim.y):
            for x in range(dim.x):
                self.grid[pos.x + x][pos.y + y] = value

    def _is_free(self, gate_id: int, pos: Dim) -> bool:
        gate = self.gates[gate_id]

        for y in range(gate.dim.y):
            for x in range(gate.dim.x):
                try:
                    if self.grid[pos.x + x][pos.y + y] != -1:
                        return False
                except IndexError:
                    return False

        return True

    def _free(self, gate_id: int) -> None:
        gate = self.gates[gate_id]
        pos = self.gate_map[gate_id]

        if pos is None:
            return

        self.gate_map[gate_id] = None
        self._set(pos, gate.dim, -1)

    def _fill(self, gate_id: int, pos: Dim) -> None:
        gate = self.gates[gate_id]
        self.gate_map[gate_id] = pos
        self._set(pos, gate.dim, gate_id)

    def _place(self, gate_id: int) -> None:
        count = 0

        while True:
            if count == 1000:
                print("ERROR: Unable to find placement for gates")
                raise ValueError

            pos = Dim(randrange(0, self.dim.x), randrange(0, self.dim.y))

            if self._is_free(gate_id, pos):
                self._fill(gate_id, pos)
                break

            count += 1

    def mutate(self) -> tuple[int, Dim, int, Dim]:
        gate_a_id = randrange(0, len(self.gates))
        gate_b_id = randrange(0, len(self.gates))

        if gate_a_id == gate_b_id:
            return self.mutate()

        gate_a_pos = self.gate_map[gate_a_id]
        gate_b_pos = self.gate_map[gate_b_id]

        if gate_a_pos is None or gate_b_pos is None:
            return self.mutate()

        self._free(gate_a_id)
        self._free(gate_b_id)

        self._place(gate_a_id)
        self._place(gate_b_id)

        return gate_a_id, gate_a_pos, gate_b_id, gate_b_pos

    def undo_mutate(
        self, gate_a_id: int, gate_a_pos: Dim, gate_b_id: int, gate_b_pos: Dim
    ) -> None:
        self._free(gate_a_id)
        self._free(gate_b_id)

        if gate_a_pos is None or gate_b_pos is None:
            return

        self._fill(gate_a_id, gate_a_pos)
        self._fill(gate_b_id, gate_b_pos)

    @property
    def cost(self) -> float:
        cost = 0.0

        for out_gate, in_gates in self.out_in_map.items():
            gates_pos = [self.gate_map[out_gate]]

            gates_pos.extend(
                [self.gate_map[in_gate_id] for in_gate_id in in_gates],
            )

            x_pos = [dim.x for dim in gates_pos if dim is not None]
            y_pos = [dim.y for dim in gates_pos if dim is not None]

            x_max, x_min = max(x_pos), min(x_pos)
            y_max, y_min = max(y_pos), min(y_pos)

            half_perim = ((x_max - x_min) + (y_max - y_min)) / 2

            cost += half_perim

        return cost

    @property
    def num_filled(self) -> int:
        return np.count_nonzero(self.grid != -1)


class RandomPlacer:
    def __init__(self) -> None:
        self.cost = math.inf

    def update(self, grid: MinecraftGrid) -> None:
        print(f"INFO: Curr cost is {self.cost}")
        print(f"INFO: {grid.num_filled} units are filled")

        a, a_pos, b, b_pos = grid.mutate()
        new_cost = grid.cost

        print("INFO: New cost is", new_cost)

        if new_cost < self.cost:
            self.cost = new_cost
            print("INFO: Keeping mutation")
        else:
            grid.undo_mutate(a, a_pos, b, b_pos)
            print("INFO: Undoing mutation")
