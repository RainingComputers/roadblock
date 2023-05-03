import dataclasses
from enum import Enum
from typing import Any
from graphviz import Graph

from roadblock.dim import Dim

CellType = Enum("CellTypes", ["BUFF", "NOT", "IN", "OUT", "DFF"])


@dataclasses.dataclass
class MinecraftCell:
    name: str
    cell_type: CellType
    # TODO: These are intermediate items, not needed really
    inputs: list[int] | None
    outputs: list[int] | None
    clk_inputs: list[int] | None

    @property
    def full_name(self) -> str:
        return self.cell_type.name.lower() + "-" + self.name

    @property
    def dim(self) -> Dim:
        if self.cell_type == CellType.NOT:
            return Dim(1, 2)

        return Dim(1, 1)

    @property
    def in_coords(self) -> Dim:
        return Dim(0, 0)

    @property
    def out_coords(self) -> Dim:
        if self.cell_type == CellType.NOT:
            return Dim(0, 1)

        return Dim(0, 0)


def get_cell_type(yosys_type: dict[str, Any]) -> CellType:
    if yosys_type == "NOT" or yosys_type == "NOR":
        return CellType.NOT

    if yosys_type == "BUFF":
        return CellType.BUFF

    if yosys_type == "DFF":
        return CellType.DFF

    if yosys_type == "input":
        return CellType.IN

    if yosys_type == "output":
        return CellType.OUT

    raise KeyError


def yosys_to_minecraft_cells(
    data: dict[str, Any],
) -> tuple[list[MinecraftCell], dict[int, list[int]]]:
    cells: list[MinecraftCell] = []

    # Given a cell id, what cells take this net as input or clk
    net_list: dict[int, list[int]] = {}  # TODO: This could be a list

    def append_to_netlist(nets: list[int], cell_id: int) -> None:
        for net in nets:
            try:
                net_list[net].append(cell_id)
            except KeyError:
                net_list[net] = [cell_id]

    for yosys_name, yosys_cell in data["modules"]["adder"]["cells"].items():
        cell_id = len(cells)

        yosys_type = yosys_cell["type"]
        yosys_connection = yosys_cell["connections"]

        if yosys_type == "DFF":
            input_nets = yosys_connection["D"]
            output_nets = yosys_connection["Q"]
            clk_nets = yosys_connection["C"]
        else:
            input_nets = yosys_connection["A"]
            output_nets = yosys_connection["Y"]
            if yosys_type == "NOR":
                input_nets.extend(yosys_connection["B"])

            clk_nets = None

        append_to_netlist(input_nets, cell_id)
        if clk_nets is not None:
            append_to_netlist(clk_nets, cell_id)

        cells.append(
            MinecraftCell(
                name=yosys_name.split("$")[-1],
                cell_type=get_cell_type(yosys_type),
                inputs=input_nets,
                outputs=output_nets,
                clk_inputs=clk_nets,
            )
        )

    for port_name, yosys_port in data["modules"]["adder"]["ports"].items():
        cell_id = len(cells)

        port_nets = yosys_port["bits"]
        port_type = get_cell_type(yosys_port["direction"])

        if port_type == CellType.IN:
            cells.append(
                MinecraftCell(
                    name=port_name,
                    cell_type=port_type,
                    inputs=None,
                    outputs=port_nets,
                    clk_inputs=None,
                )
            )
        else:
            append_to_netlist(port_nets, cell_id)

            cells.append(
                MinecraftCell(
                    name=port_name,
                    cell_type=port_type,
                    inputs=port_nets,
                    outputs=None,
                    clk_inputs=None,
                )
            )

    return cells, net_list


def construct_out_in_map(
    cells: list[MinecraftCell], net_list: dict[int, list[int]]
) -> dict[int, set[int]]:
    # Given a cell, what other cells take its output as input or clock
    out_in_map: dict[int, set[int]] = {}

    for cell_id, cell in enumerate(cells):
        if cell.outputs is None:
            continue

        for out_net in cell.outputs:
            try:
                out_in_map[cell_id] = set(net_list[out_net])
            except KeyError:
                print(
                    f"WARN: Inputs not found for {cell.name} net {out_net}",
                )

    return out_in_map


def show_circuit(
    out_in_map: dict[int, set[int]],
    cells: list[MinecraftCell],
) -> None:
    g = Graph()

    for out_cell, in_cells in out_in_map.items():
        for in_cell in in_cells:
            g.edge(cells[out_cell].full_name, cells[in_cell].full_name)

    g.view()
