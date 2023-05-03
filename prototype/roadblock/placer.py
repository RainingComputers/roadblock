from random import randrange
import math

import numpy as np

from roadblock.dim import Dim
from roadblock.netlist import MinecraftCell


class MinecraftGrid:
    dim: Dim
    grid: np.ndarray
    cells: list[MinecraftCell]
    out_in_map: dict[int, set[int]]

    def __init__(
        self,
        dim: Dim,
        cells: list[MinecraftCell],
        in_out_map: dict[int, set[int]],
    ):
        self.dim = dim
        self.in_out_map = in_out_map
        self.cells = cells

        self.grid = np.full((dim.x, dim.y), -1)
        self.cell_map: list[Dim | None] = [None] * len(cells)

        for cell_id in range(len(cells)):
            self._place(cell_id)

    def _set(self, pos: Dim, dim: Dim, value: int) -> None:
        for y in range(dim.y):
            for x in range(dim.x):
                self.grid[pos.x + x][pos.y + y] = value

    def _is_free(self, cell_id: int, pos: Dim) -> bool:
        cell = self.cells[cell_id]

        for y in range(cell.dim.y):
            for x in range(cell.dim.x):
                try:
                    if self.grid[pos.x + x][pos.y + y] != -1:
                        return False
                except IndexError:
                    return False

        return True

    def _free(self, cell_id: int) -> None:
        cell = self.cells[cell_id]
        pos = self.cell_map[cell_id]

        if pos is None:
            return

        self.cell_map[cell_id] = None
        self._set(pos, cell.dim, -1)

    def _fill(self, cell_id: int, pos: Dim) -> None:
        cell = self.cells[cell_id]
        self.cell_map[cell_id] = pos
        self._set(pos, cell.dim, cell_id)

    def _place(self, cell_id: int) -> None:
        count = 0

        while True:
            if count == 1000:
                print("ERROR: Unable to find placement for cells")
                raise ValueError

            pos = Dim(randrange(0, self.dim.x), randrange(0, self.dim.y))

            if self._is_free(cell_id, pos):
                self._fill(cell_id, pos)
                break

            count += 1

    def mutate(self) -> tuple[int, Dim, int, Dim]:
        cell_a_id = randrange(0, len(self.cells))
        cell_b_id = randrange(0, len(self.cells))

        if cell_a_id == cell_b_id:
            return self.mutate()

        cell_a_pos = self.cell_map[cell_a_id]
        cell_b_pos = self.cell_map[cell_b_id]

        if cell_a_pos is None or cell_b_pos is None:
            return self.mutate()

        self._free(cell_a_id)
        self._free(cell_b_id)

        self._place(cell_a_id)
        self._place(cell_b_id)

        return cell_a_id, cell_a_pos, cell_b_id, cell_b_pos

    def undo_mutate(
        self, cell_a_id: int, cell_a_pos: Dim, cell_b_id: int, cell_b_pos: Dim
    ) -> None:
        self._free(cell_a_id)
        self._free(cell_b_id)

        if cell_a_pos is None or cell_b_pos is None:
            return

        self._fill(cell_a_id, cell_a_pos)
        self._fill(cell_b_id, cell_b_pos)

    @property
    def cost(self) -> float:
        cost = 0.0

        for out_cell, in_cells in self.in_out_map.items():
            cells_pos = [self.cell_map[out_cell]]

            cells_pos.extend(
                [self.cell_map[in_cell_id] for in_cell_id in in_cells],
            )

            x_pos = [dim.x for dim in cells_pos if dim is not None]
            y_pos = [dim.y for dim in cells_pos if dim is not None]

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
