from enum import Enum
from dataclasses import dataclass, field
from queue import PriorityQueue

import numpy as np

from roadblock.dim import Dim
from roadblock.grid import MinecraftGrid
from roadblock import log


Pred = Enum("Pred", ["ROOT", "NORTH", "SOUTH", "EAST", "WEST", "UP", "DOWN"])


@dataclass(order=True)
class WavefrontCell:
    layer: int = field(compare=False)
    loc: Dim = field(compare=False)
    cost: int
    pred: Pred = field(compare=False)


def construct_routes(grid: MinecraftGrid) -> list[list[Dim]]:
    wire_routes: list[list[Dim]] = []
    clk_routes: list[list[Dim]] = []

    for out_gate_id, in_gate_ids in grid.out_in_map:
        out_gate = grid.get_gate_from_id(out_gate_id)
        out_gate_pos = grid.get_pos_expect(out_gate_id)
        src = out_gate_pos + out_gate.out_coords

        wire_points: list[Dim] = [src]
        clk_points: list[Dim] = [src]

        for in_gate_id in in_gate_ids:
            in_gate = grid.get_gate_from_id(in_gate_id)
            in_gate_pos = grid.get_pos_expect(in_gate_id)

            if out_gate.outputs & in_gate.inputs:
                wire_points.append(in_gate_pos + in_gate.in_coords)

            if out_gate.outputs & in_gate.clk_inputs:
                clk_points.append(in_gate_pos + in_gate.clk_coords)

        if len(wire_points) != 0:
            wire_routes.append(wire_points)

        if len(clk_points) != 0:
            clk_routes.append(clk_points)

    all_routes = clk_routes
    all_routes.extend(wire_routes)

    return all_routes


def create_pred_grid(
    dim: Dim, max_layers: int, roots: list[tuple[int, int, int]]
) -> np.ndarray[Pred | None]:
    create_cell_vec = np.vectorize(lambda _: None)
    pred_grid = create_cell_vec(np.full((dim.x, dim.y, max_layers), 0))

    for root in roots:
        pred_grid[root[0], root[1], root[2]] = Pred.ROOT

    return pred_grid


def neighbors(
    cell: WavefrontCell,
    router_grid: np.ndarray[int],
    pred_grid: np.ndarray[Pred | None],
) -> list[WavefrontCell]:
    return []


def backtrace_inplace(
    target: WavefrontCell,
    router_grid: np.ndarray[int],
    pred_grid: np.ndarray[Pred | None],
) -> list[tuple[int, int, int]]:
    return []


def reset_wavefront_inplace(
    wavefront: PriorityQueue[WavefrontCell],
    traces: list[tuple[int, int, int]],
) -> None:
    wavefront.queue.clear()

    for point in traces:
        wavefront.put(
            WavefrontCell(
                layer=point[2], loc=Dim(point[0], point[1]), cost=0, pred=Pred.ROOT
            )
        )


def route(grid: MinecraftGrid, dim: Dim, max_layers: int) -> None:
    router_grid = np.full((dim.x, dim.y, max_layers), -1)

    routes = construct_routes(grid)

    for points in routes:
        start = points[0]
        targets = points[1:]

        traces: list[tuple[int, int, int]] = [(start.x, start.y, 0)]
        wavefront: PriorityQueue[WavefrontCell] = PriorityQueue()

        pred_grid = create_pred_grid(dim, max_layers, traces)
        wavefront.put(WavefrontCell(layer=0, loc=start, cost=0, pred=Pred.ROOT))

        reached = False

        while not reached:
            if wavefront.empty():
                log.error("Reached empty wavefront")
                raise ValueError

            cell = wavefront.get()

            if cell.loc in targets:
                targets.remove(cell.loc)

                traces.extend(backtrace_inplace(cell, router_grid, pred_grid))

                pred_grid = create_pred_grid(dim, max_layers, traces)
                reset_wavefront_inplace(wavefront, traces)

                if len(targets) == 0:
                    reached = True

                break

            for unreached_cell in neighbors(cell, router_grid, pred_grid):
                wavefront.put(unreached_cell)

            pred_grid[cell.loc.x][cell.loc.y][cell.layer].pred = cell.pred
