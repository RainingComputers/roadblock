import random
from enum import Enum
from dataclasses import dataclass, field
from queue import PriorityQueue, Queue

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


def construct_routes(grid: GatesGrid) -> dict[int, list[Dim]]:
    routes: dict[int, list[Dim]] = {}

    for net_id, gates_ids in grid.netlist:
        points: list[Dim] = []

        for gate_id in gates_ids:
            gate = grid.get_gate_from_id(gate_id)
            gate_pos = grid.get_pos_expect(gate_id)

            if net_id in gate.inputs:
                points.append(gate_pos + gate.in_coords)

            if net_id in gate.outputs:
                points.append(gate_pos + gate.out_coords)

            if net_id in gate.clk_inputs:
                points.append(gate_pos + gate.clk_coords)

        routes[net_id] = points

    return routes


def create_router_grid(dim: Dim, max_layers: int) -> np.ndarray[int]:
    return np.full((max_layers, dim.x, dim.y), -1, dtype=np.int32)


def create_pred_grid(
    dim: Dim, max_layers: int, roots: list[Dim3]
) -> np.ndarray[Pred | None]:
    create_cell_vec = np.vectorize(lambda _: None)
    pred_grid = create_cell_vec(np.full((dim.x, dim.y, max_layers), 0))

    for root in roots:
        pred_grid[root.x, root.y, root.z] = Pred.ROOT

    return pred_grid


def get_neighbors(
    cell: WavefrontCell,
    router_grid: np.ndarray[int],
    pred_grid: np.ndarray[Pred | None],
    wavefront_locs: list[Dim3],
) -> list[WavefrontCell]:
    neighbors_preds = [pred for pred in Pred if pred != Pred.ROOT]

    neighbors: list[WavefrontCell] = []

    for pred in neighbors_preds:
        nloc = cell.loc - pred_to_dim3(pred)

        if nloc.x < 0 or nloc.y < 0 or nloc.z < 0:
            continue

        if (
            nloc.x >= router_grid.shape[1]
            or nloc.y >= router_grid.shape[2]
            or nloc.z >= router_grid.shape[0]
        ):
            continue

        if router_grid[nloc.z, nloc.x, nloc.y] != -1:
            continue

        if pred_grid[nloc.x, nloc.y, nloc.z] is not None:
            continue

        if nloc in wavefront_locs:
            continue

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

    router_grid[loc.z, loc.x, loc.y] = route_id

    while pred != Pred.ROOT:
        new_loc = loc + pred_to_dim3(pred)

        pred = pred_grid[new_loc.x, new_loc.y, new_loc.z]

        if pred != Pred.ROOT:
            trace.append(new_loc)

        router_grid[new_loc.z, new_loc.x, new_loc.y] = route_id
        loc = new_loc

    return trace


def reset_wavefront_inplace(
    wavefront: PriorityQueue[WavefrontCell],
    traces: list[Dim3],
) -> None:
    wavefront.queue.clear()

    for point in traces:
        wavefront.put(WavefrontCell(loc=point, cost=0, pred=Pred.ROOT))


def dump_router_grid(router_grid: np.ndarray[int]) -> None:
    for i in range(router_grid.shape[0]):
        np.savetxt(f"routes-layer{i}.txt", router_grid[i], fmt="%d")


def create_route_inplace(
    router_grid: np.ndarray[Pred | None],
    route_id: int,
    points: list[Dim],
    grid_dim: Dim,
    max_layers: int,
) -> bool:
    start = points[0].to_dim3()
    targets = list(map(lambda point: point.to_dim3(), points[1:]))

    traces: list[Dim3] = [start]
    wavefront: PriorityQueue[WavefrontCell] = PriorityQueue()

    pred_grid = create_pred_grid(grid_dim, max_layers, traces)
    wavefront.put(WavefrontCell(loc=start, cost=0, pred=Pred.ROOT))

    while True:
        if wavefront.empty():
            dump_router_grid(router_grid)
            return False

        cell = wavefront.get()

        if cell.loc in targets:
            targets.remove(cell.loc)

            traces.extend(backtrace_inplace(cell, router_grid, pred_grid, route_id))

            pred_grid = create_pred_grid(grid_dim, max_layers, traces)
            reset_wavefront_inplace(wavefront, traces)

            if len(targets) == 0:
                return True

        wavefront_locs = list(map(lambda cell: cell.loc, wavefront.queue))

        neighbors = get_neighbors(cell, router_grid, pred_grid, wavefront_locs)

        for neighbor in neighbors:
            wavefront.put(neighbor)

        pred_grid[cell.loc.x, cell.loc.y, cell.loc.z] = cell.pred


def rip_route_inplace(router_grid: np.ndarray[int], route_id: int) -> None:
    router_grid[router_grid == route_id] = -1


def route(grid: GatesGrid, max_layers: int) -> None:
    router_grid = create_router_grid(grid.dim, max_layers)

    routes = construct_routes(grid)
    route_queue: Queue[tuple[int, list[Dim]]] = Queue()
    for route_id, points in routes.items():
        route_queue.put((route_id, points))

    created_routes: set[int] = set()

    log.info(f"Routing {route_queue.qsize()} routes")

    while route_queue.qsize() != 0:
        route_id, points = route_queue.get()
        route_created = create_route_inplace(
            router_grid, route_id, points, grid.dim, max_layers
        )

        if not route_created:
            # route_id_to_rip = random.choice(list(created_routes))
            # log.info(
            #     f"Unable to route {route_id}, ripping random route {route_id_to_rip}"
            # )

            # created_routes.remove(route_id_to_rip)
            # rip_route_inplace(router_grid, route_id_to_rip)
            # rip_route_inplace(router_grid, route_id)

            # route_queue.put((route_id, points))
            # route_queue.put((route_id_to_rip, routes[route_id_to_rip]))
            # log.info(f"Route queue size is now {route_queue.qsize()}")

            log.info(f"Unable to route {route_id} ripping all routes")

            route_queue.put((route_id, points))

            for other_route_id in created_routes:
                route_queue.put((other_route_id, routes[other_route_id]))

            router_grid = create_router_grid(grid.dim, max_layers)
            created_routes = set()
        else:
            log.info(f"Created route {route_id}")
            created_routes.add(route_id)
