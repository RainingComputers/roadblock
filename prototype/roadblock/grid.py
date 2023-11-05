from random import randrange
from typing import Iterator, ItemsView

import numpy as np

from roadblock.dim import Dim
from roadblock.netlist import MinecraftGate, construct_in_out_map

from roadblock import log


def dim_pin_iterator(dim: Dim) -> Iterator[Dim]:
    for x in range(dim.x):
        yield Dim(x, 0)

    for y in range(1, dim.y):
        yield Dim(dim.x - 1, y)

    for x in range(dim.x - 2, -1, -1):
        yield Dim(x, dim.y - 1)

    for y in range(dim.y - 2, -1, -1):
        yield Dim(0, y)

    log.error("Not enough pin space")
    raise ValueError


def is_pin_coords(pos: Dim, dim: Dim) -> bool:
    return pos.x == 0 or pos.y == 0 or pos.x == dim.x - 1 or pos.y == dim.y - 1


def get_half_perim(gates_pos: list[Dim | None]) -> float:
    x_pos = [dim.x for dim in gates_pos if dim is not None]
    y_pos = [dim.y for dim in gates_pos if dim is not None]

    x_max, x_min = max(x_pos), min(x_pos)
    y_max, y_min = max(y_pos), min(y_pos)

    half_perim = ((x_max - x_min) + (y_max - y_min)) / 2
    return half_perim


def get_affected_gates(
    gate_id: int,
    in_out_map: dict[int, set[int]],
) -> list[int]:
    ids = [gate_id]
    ids.extend(in_out_map[gate_id])

    return ids


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
        self._in_out_map = construct_in_out_map(out_in_map)
        self._gates = gates

        self._grid = np.full((dim.x, dim.y), -1)
        self._gate_pos_map: list[Dim | None] = [None] * self.num_gates

        pins = dim_pin_iterator(dim)

        for gate_id, gate in enumerate(gates):
            if gate.is_port:
                pos = next(pins)
                self._fill(gate_id, pos)
            else:
                self._place(gate_id)

        self._cost_cache = MinecraftGridCostCache(out_in_map, self._gate_pos_map)

    @property
    def out_in_map(self) -> ItemsView[int, set[int]]:
        return self._out_in_map.items()

    @property
    def num_gates(self) -> int:
        return len(self._gates)

    @property
    def dim(self) -> Dim:
        return self._dim

    def get_pos(self, gate_id: int) -> Dim | None:
        return self._gate_pos_map[gate_id]

    def get_pos_expect(self, gate_id: int) -> Dim:
        pos = self._gate_pos_map[gate_id]

        if pos is None:
            log.error(f"Gate {gate_id} has not been placed yey")
            raise ValueError

        return pos

    def get_gate_from_id(self, gate_id: int) -> MinecraftGate:
        return self._gates[gate_id]

    def get_gate_id_from_pos(self, pos: Dim) -> int | None:
        if pos.x >= self._dim.x or pos.x < 0:
            return None

        if pos.y >= self._dim.y or pos.y < 0:
            return None

        gate_id = self._grid[pos.x][pos.y]

        if gate_id >= self.num_gates or gate_id < 0:
            return None

        return gate_id

    @property
    def cost(self) -> float:
        return self._cost_cache.cached_cost(self._out_in_map, self._gate_pos_map)

    @property
    def num_filled(self) -> int:
        return np.count_nonzero(self._grid != -1)

    def mutate(self) -> tuple[int, Dim, int, Dim]:
        gate_a_id = randrange(0, len(self._gates))
        gate_b_id = randrange(0, len(self._gates))

        if self._gates[gate_a_id].is_port or self._gates[gate_b_id].is_port:
            return self.mutate()

        if gate_a_id == gate_b_id:
            return self.mutate()

        gate_a_pos = self._gate_pos_map[gate_a_id]
        gate_b_pos = self._gate_pos_map[gate_b_id]

        if gate_a_pos is None or gate_b_pos is None:
            log.error("Corrupt state found while trying to mutate grid")
            raise ValueError

        self._cost_cache.being_mutation([gate_a_id, gate_b_id], self._in_out_map)

        self._move_gate(gate_a_id)
        self._move_gate(gate_b_id)

        self._cost_cache.end_mutation_and_update_cache()

        return gate_a_id, gate_a_pos, gate_b_id, gate_b_pos

    def _move_gate(self, gate_id: int) -> None:
        self._cost_cache.begin_gate_move(gate_id, self._in_out_map)

        self._free(gate_id)
        self._place(gate_id)

        self._cost_cache.end_gate_move(
            gate_id, self._in_out_map, self._out_in_map, self._gate_pos_map
        )

    def undo_mutate(
        self, gate_a_id: int, gate_a_pos: Dim, gate_b_id: int, gate_b_pos: Dim
    ) -> None:
        self._free(gate_a_id)
        self._free(gate_b_id)

        self._fill(gate_a_id, gate_a_pos)
        self._fill(gate_b_id, gate_b_pos)

        self._cost_cache.undo_mutation_and_update_cache()

    def _set(self, pos: Dim, dim: Dim, value: int) -> None:
        for y in range(dim.y):
            for x in range(dim.x):
                self._grid[pos.x + x][pos.y + y] = value

    def _is_free(self, gate_id: int, pos: Dim) -> bool:
        gate = self._gates[gate_id]

        for y in range(gate.dim.y):
            for x in range(gate.dim.x):
                if is_pin_coords(Dim(pos.x + x, pos.y + y), self._dim):
                    return False

                try:
                    if self._grid[pos.x + x][pos.y + y] != -1:
                        return False
                except IndexError:
                    return False

        return True

    def _free(self, gate_id: int) -> None:
        gate = self._gates[gate_id]
        pos = self._gate_pos_map[gate_id]

        log.debug(f"Remove gate {gate_id} at {pos}")

        if pos is None:
            return

        self._gate_pos_map[gate_id] = None
        self._set(pos, gate.dim, -1)

    def _fill(self, gate_id: int, pos: Dim) -> None:
        gate = self._gates[gate_id]
        self._gate_pos_map[gate_id] = pos
        self._set(pos, gate.dim, gate_id)

    def _place(self, gate_id: int) -> None:
        count = 0

        while True:
            if count == MinecraftGrid.PLACE_RETRY_COUNT:
                log.error(f"Unable to find placement for gate {gate_id}")
                raise ValueError

            pos = Dim(randrange(0, self._dim.x), randrange(0, self._dim.y))

            if self._is_free(gate_id, pos):
                self._fill(gate_id, pos)
                log.debug(f"Place gate {gate_id} at {pos}")
                break

            count += 1


class MinecraftGridCostCache:
    def __init__(
        self, out_in_map: dict[int, set[int]], gate_pos_map: list[Dim | None]
    ) -> None:
        self._half_perim_cache_map: dict[int, float] = {}

        self._undo_half_perim_map: dict[int, float] = {}
        self._undo_cost_old = 0.0
        self._undo_cost_new = 0.0

        self._cost_cache: float = self.cost_clean(out_in_map, gate_pos_map)

    def cost_clean(
        self, out_in_map: dict[int, set[int]], gate_pos_map: list[Dim | None]
    ) -> float:
        log.info("Calculating clean grid cost")

        cost = 0.0

        for out_gate_id in out_in_map:
            cost += self._get_and_cache_gate_half_perim(
                out_gate_id, out_in_map, gate_pos_map
            )

        return cost

    def cached_cost(
        self, out_in_map: dict[int, set[int]], gate_pos_map: list[Dim | None]
    ) -> float:
        cost_clean = self.cost_clean(out_in_map, gate_pos_map)
        self._cost_cache = cost_clean
        return cost_clean

    def being_mutation(
        self, gate_ids: list[int], in_out_map: dict[int, set[int]]
    ) -> None:
        self._undo_cost_old = 0.0
        self._undo_cost_new = 0.0
        self._undo_half_perim_map.clear()

        for gate_id in gate_ids:
            self._save_affected_half_perims(gate_id, in_out_map)

    def begin_gate_move(self, gate_id: int, in_out_map: dict[int, set[int]]) -> None:
        if self._cost_cache is not None:
            self._undo_cost_old += self._get_cached_part_cost(gate_id, in_out_map)

    def end_gate_move(
        self,
        gate_id: int,
        in_out_map: dict[int, set[int]],
        out_in_map: dict[int, set[int]],
        gate_pos_map_after: list[Dim | None],
    ) -> None:
        self._undo_cost_new += self._get_part_cost(
            gate_id, in_out_map, out_in_map, gate_pos_map_after
        )

    def end_mutation_and_update_cache(self) -> None:
        self._cost_cache -= self._undo_cost_old
        self._cost_cache += self._undo_cost_new

    def undo_mutation_and_update_cache(self) -> None:
        self._cost_cache -= self._undo_cost_new
        self._cost_cache += self._undo_cost_old

        self._restore_half_perims()

    def _get_and_cache_gate_half_perim(
        self,
        out_gate_id: int,
        out_in_map: dict[int, set[int]],
        gate_pos_map: list[Dim | None],
    ) -> float:
        gates_pos_list = [gate_pos_map[out_gate_id]]

        in_gates_ids = out_in_map[out_gate_id]

        gates_pos_list.extend(
            [gate_pos_map[in_gate_id] for in_gate_id in in_gates_ids],
        )

        half_perim = get_half_perim(gates_pos_list)
        self._half_perim_cache_map[out_gate_id] = half_perim

        return half_perim

    def _get_cached_part_cost(
        self,
        gate_id: int,
        in_out_map: dict[int, set[int]],
    ) -> float:
        ids = get_affected_gates(gate_id, in_out_map)
        return sum([self._half_perim_cache_map[gate_id] for gate_id in ids])

    def _get_part_cost(
        self,
        gate_id: int,
        in_out_map: dict[int, set[int]],
        out_in_map: dict[int, set[int]],
        gate_pos_map: list[Dim | None],
    ) -> float:
        ids = get_affected_gates(gate_id, in_out_map)
        return sum(
            [
                self._get_and_cache_gate_half_perim(gate_id, out_in_map, gate_pos_map)
                for gate_id in ids
            ]
        )

    def _save_affected_half_perims(
        self,
        gate_id: int,
        in_out_map: dict[int, set[int]],
    ) -> None:
        ids = get_affected_gates(gate_id, in_out_map)

        for gate_id in ids:
            self._undo_half_perim_map[gate_id] = self._half_perim_cache_map[gate_id]

    def _restore_half_perims(self) -> None:
        for gate_id, half_perim in self._undo_half_perim_map.items():
            self._half_perim_cache_map[gate_id] = half_perim
