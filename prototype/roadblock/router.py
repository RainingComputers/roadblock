from enum import Enum
from dataclasses import dataclass, field
from queue import PriorityQueue

import numpy as np

from roadblock.dim import Dim, Dim3
from roadblock.grid import GatesGrid
from roadblock import log


Pred = Enum("Pred", ["ROOT", "NORTH", "SOUTH", "EAST", "WEST", "UP", "DOWN"])


@dataclass(order=True)
class WavefrontCell:
    loc: Dim3 = field(compare=False)
    cost: int
    pred: Pred = field(compare=False)


def pred_to_dim3(pred: Pred) -> Dim3:
    if pred == Pred.ROOT:
        return Dim3(x=0, y=0, z=0)
    if pred == Pred.NORTH:
        return Dim3(x=0, y=-1, z=0)
    if pred == Pred.SOUTH:
        return Dim3(x=0, y=1, z=0)
    if pred == Pred.EAST:
        return Dim3(x=1, y=0, z=0)
    if pred == Pred.WEST:
        return Dim3(x=-1, y=0, z=0)
    if pred == Pred.UP:
        return Dim3(x=0, y=0, z=1)
    if pred == Pred.DOWN:
        return Dim3(x=0, y=0, z=-1)

    raise ValueError


def pred_to_cost(pred: Pred) -> int:
    if pred == Pred.UP or pred == Pred.DOWN:
        return 3

    return 1


def construct_routes(grid: GatesGrid) -> list[list[Dim]]:
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
    dim: Dim, max_layers: int, roots: list[Dim3]
) -> np.ndarray[Pred | None]:
    create_cell_vec = np.vectorize(lambda _: None)
    pred_grid = create_cell_vec(np.full((dim.x, dim.y, max_layers), 0))

    for root in roots:
        pred_grid[root.x, root.y, root.z] = Pred.ROOT

    return pred_grid


def neighbors(
    cell: WavefrontCell,
    router_grid: np.ndarray[int],
    pred_grid: np.ndarray[Pred | None],
) -> list[WavefrontCell]:
    neighbors_preds = [pred for pred in Pred if pred != Pred.ROOT]

    neighbors: list[WavefrontCell] = []

    for pred in neighbors_preds:
        nloc = cell.loc - pred_to_dim3(pred)

        if router_grid[nloc.x, nloc.y, nloc.z] != -1:
            continue

        if pred_grid[nloc.x, nloc.y, nloc.z] is not None:
            continue

        # cap with grid limits

        neighbors.append(WavefrontCell(loc=nloc, cost=pred_to_cost(pred), pred=pred))

    return neighbors


def backtrace_inplace(
    target: WavefrontCell,
    router_grid: np.ndarray[int],
    pred_grid: np.ndarray[Pred | None],
    route_id: int,
) -> list[Dim3]:
    pred: Pred = target.pred
    loc: Dim3 = target.loc
    trace: list[Dim3] = [loc]

    router_grid[loc.x, loc.y, loc.z] = route_id

    while pred != Pred.ROOT:
        new_loc = loc + pred_to_dim3(pred)

        trace.append(new_loc)
        router_grid[new_loc.x, new_loc.y, new_loc.z] = route_id

        pred = pred_grid[loc.x, loc.y, loc.z]
        loc = new_loc

    return trace


def reset_wavefront_inplace(
    wavefront: PriorityQueue[WavefrontCell],
    traces: list[Dim3],
) -> None:
    wavefront.queue.clear()

    for point in traces:
        wavefront.put(WavefrontCell(loc=point, cost=0, pred=Pred.ROOT))


def route(grid: GatesGrid, dim: Dim, max_layers: int) -> None:
    router_grid = np.full((dim.x, dim.y, max_layers), -1)

    routes = construct_routes(grid)

    for route_id, points in enumerate(routes):
        start = points[0].to_dim3()
        targets = list(map(lambda point: point.to_dim3(), points[1:]))

        traces: list[Dim3] = [start]
        wavefront: PriorityQueue[WavefrontCell] = PriorityQueue()

        pred_grid = create_pred_grid(dim, max_layers, traces)
        wavefront.put(WavefrontCell(loc=start, cost=0, pred=Pred.ROOT))

        reached = False

        while not reached:
            if wavefront.empty():
                log.error("Reached empty wavefront")
                raise ValueError

            cell = wavefront.get()

            if cell.loc in targets:
                targets.remove(cell.loc)

                traces.extend(backtrace_inplace(cell, router_grid, pred_grid, route_id))

                pred_grid = create_pred_grid(dim, max_layers, traces)
                reset_wavefront_inplace(wavefront, traces)

                if len(targets) == 0:
                    reached = True

                break

            for unreached_cell in neighbors(cell, router_grid, pred_grid):
                wavefront.put(unreached_cell)

            pred_grid[cell.loc.x, cell.loc.y, cell.loc.z].pred = cell.pred
