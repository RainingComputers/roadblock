# from roadblock.dim import Dim
# from roadblock.grid import MinecraftGrid
# from dataclasses import dataclass
# from enum import Enum


# @dataclass
# class Via:
#     source: int
#     dest: int


# RouteType = Enum("RouteType", ["WIRE", "CLK"])


# @dataclass
# class Route:
#     src: tuple[int, int, int]
#     dest: tuple[int, int, int]
#     type: RouteType


# class Router:
#     def __init__(self, dim: Dim, max_layers: int) -> None:
#         self._dim = dim
#         self._max_layers = max_layers

#         self._route_grid: list[list[list[int | Via]]] = [
#             [[-1] * dim.y] * dim.x
#         ] * max_layers

#     # TODO: Refactor this
#     def _construct_routes(self, grid: MinecraftGrid) -> list[Route]:
#         routes: list[Route] = []

#         for out_gate_id, in_gate_ids in grid._out_in_map.items():
#             for in_gate_id in in_gate_ids:
#                 in_gate = grid.get_gate_from_id(in_gate_id)
#                 out_gate = grid.get_gate_from_id(out_gate_id)

#                 in_gate_pos = grid.get_pos(in_gate_id)
#                 out_gate_pos = grid.get_pos(out_gate_id)

#                 if set(in_gate.inputs) & set(out_gate.outputs):
#                     out_pos = out_gate_pos + out_gate.out_coords
#                     in_pos = in_gate_pos + in_gate.in_coords
#                     routes.append(
#                         Route(
#                             src=(
#                                 0,
#                                 out_pos.x,
#                                 out_pos.y,
#                             ),
#                             dest=(
#                                 0,
#                                 in_pos.x,
#                                 in_pos.y,
#                             ),
#                             type=RouteType.WIRE,
#                         )
#                     )

#                 if set(in_gate.clk_inputs) & set(out_gate.outputs):
#                     out_pos = out_gate_pos + out_gate.out_coords
#                     clk_pos = in_gate_pos + in_gate.in_coords
#                     routes.append(
#                         Route(
#                             src=(
#                                 0,
#                                 out_pos.x,
#                                 out_pos.y,
#                             ),
#                             dest=(
#                                 0,
#                                 clk_pos.x,
#                                 clk_pos.y,
#                             ),
#                             type=RouteType.CLK,
#                         )
#                     )

#         return routes

#     def route(grid: MinecraftGrid) -> None:
#         pass
