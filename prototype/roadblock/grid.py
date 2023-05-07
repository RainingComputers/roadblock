from random import randrange
from typing import Iterator

import numpy as np

from roadblock.dim import Dim
from roadblock.netlist import MinecraftGate


def dim_pin_iterator(dim: Dim) -> Iterator[Dim]:
    for x in range(dim.x):
        yield Dim(x, 0)

    for y in range(1, dim.y):
        yield Dim(dim.x - 1, y)

    for x in range(dim.x - 2, -1, -1):
        yield Dim(x, dim.y - 1)

    for y in range(dim.y - 2, -1, -1):
        yield Dim(0, y)

    print("ERROR: Not enough pin space")
    raise ValueError


def is_pin_coords(pos: Dim, dim: Dim) -> bool:
    return pos.x == 0 or pos.y == 0 or pos.x == dim.x - 1 or pos.y == dim.y - 1


class MinecraftGrid:
    PLACE_RETRY_COUNT = 1000

    def __init__(
        self,
        dim: Dim,
        gates: list[MinecraftGate],
        out_in_map: dict[int, set[int]],
    ):
        self._dim = dim
        self._out_in_map = out_in_map
        self._gates = gates

        self._grid = np.full((dim.x, dim.y), -1)
        self._gate_map: list[Dim | None] = [None] * self.num_gates

        pins = dim_pin_iterator(dim)

        for gate_id, gate in enumerate(gates):
            if gate.is_port:
                pos = next(pins)
                self._fill(gate_id, pos)
            else:
                self._place(gate_id)

    @property
    def num_gates(self) -> int:
        return len(self._gates)

    @property
    def dim(self) -> Dim:
        return self._dim

    def get_pos(self, gate_id: int) -> Dim | None:
        return self._gate_map[gate_id]

    def get_gate_from_id(self, gate_id: int) -> MinecraftGate:
        return self._gates[gate_id]

    def get_gate_from_pos(self, pos: Dim) -> int | None:
        if pos.x >= self._dim.x or pos.x < 0:
            None

        if pos.y >= self._dim.y or pos.y < 0:
            return None

        gate_id = self._grid[pos.x][pos.y]

        if gate_id >= self.num_gates or gate_id < 0:
            return None

        return gate_id

    def _set(self, pos: Dim, dim: Dim, value: int) -> None:
        for y in range(dim.y):
            for x in range(dim.x):
                self._grid[pos.x + x][pos.y + y] = value

    def _is_free(self, gate_id: int, pos: Dim) -> bool:
        if is_pin_coords(pos, self._dim):
            return False

        gate = self._gates[gate_id]

        for y in range(gate.dim.y):
            for x in range(gate.dim.x):
                try:
                    if self._grid[pos.x + x][pos.y + y] != -1:
                        return False
                except IndexError:
                    return False

        return True

    def _free(self, gate_id: int) -> None:
        gate = self._gates[gate_id]
        pos = self._gate_map[gate_id]

        if pos is None:
            return

        self._gate_map[gate_id] = None
        self._set(pos, gate.dim, -1)

    def _fill(self, gate_id: int, pos: Dim) -> None:
        gate = self._gates[gate_id]
        self._gate_map[gate_id] = pos
        self._set(pos, gate.dim, gate_id)

    def _place(self, gate_id: int) -> None:
        count = 0

        while True:
            if count == MinecraftGrid.PLACE_RETRY_COUNT:
                print("ERROR:  Unable to find placement for gates")
                raise ValueError

            pos = Dim(randrange(0, self._dim.x), randrange(0, self._dim.y))

            if self._is_free(gate_id, pos):
                self._fill(gate_id, pos)
                break

            count += 1

    def mutate(self) -> tuple[int, Dim, int, Dim]:
        gate_a_id = randrange(0, len(self._gates))
        gate_b_id = randrange(0, len(self._gates))

        if self._gates[gate_a_id].is_port or self._gates[gate_b_id].is_port:
            return self.mutate()

        if gate_a_id == gate_b_id:
            return self.mutate()

        gate_a_pos = self._gate_map[gate_a_id]
        gate_b_pos = self._gate_map[gate_b_id]

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

        for out_gate, in_gates in self._out_in_map.items():
            gates_pos = [self._gate_map[out_gate]]

            gates_pos.extend(
                [self._gate_map[in_gate_id] for in_gate_id in in_gates],
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
        return np.count_nonzero(self._grid != -1)
