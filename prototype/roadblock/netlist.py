from typing import Any
from dataclasses import dataclass
from enum import Enum

from roadblock.dim import Dim

from roadblock import log


GateType = Enum("GateType", ["BUFF", "NOT", "DFF", "IN", "OUT"])


@dataclass
class MinecraftGate:
    name: str
    gate_type: GateType
    inputs: set[int]
    outputs: set[int]
    clk_inputs: set[int]

    @property
    def full_name(self) -> str:
        return self.gate_type.name.lower() + "-" + self.name

    @property
    def dim(self) -> Dim:
        if self.gate_type == GateType.NOT:
            return Dim(1, 2)

        return Dim(1, 1)

    @property
    def in_coords(self) -> Dim:
        if self.gate_type == GateType.IN:
            log.error(f"Expected in coords for {self.gate_type}")
            raise ValueError

        return Dim(0, 0)

    @property
    def out_coords(self) -> Dim:
        if self.gate_type == GateType.OUT:
            log.error(f"Expected out coords for {self.gate_type}")
            raise ValueError

        if self.gate_type == GateType.NOT:
            return Dim(0, 1)

        return Dim(0, 0)

    @property
    def clk_coords(self) -> Dim:
        raise ValueError(f"Expected clk coords for {self.gate_type}")

    @property
    def is_port(self) -> bool:
        return self.gate_type == GateType.IN or self.gate_type == GateType.OUT


def get_gate_type(yosys_type: str) -> GateType:
    if yosys_type == "NOT" or yosys_type == "NOR":
        return GateType.NOT

    if yosys_type == "BUFF":
        return GateType.BUFF

    if yosys_type == "DFF":
        return GateType.DFF

    if yosys_type == "input":
        return GateType.IN

    if yosys_type == "output":
        return GateType.OUT

    log.error(f"Unexpected yosys gate type {yosys_type}")
    raise KeyError


def construct_nor_inputs_equals_list(
    data: dict[str, Any], module: str
) -> list[list[int]]:
    equals_list: list[list[int]] = []

    for yosys_gate in data["modules"][module]["cells"].values():
        yosys_type = yosys_gate["type"]
        yosys_connection = yosys_gate["connections"]

        if yosys_type != "NOR":
            continue

        lhs = yosys_connection["A"][0]
        rhs = yosys_connection["B"][0]

        already_exists = False

        for existing_entry in equals_list:
            if lhs in existing_entry or rhs in existing_entry:
                existing_entry.append(lhs)
                existing_entry.append(rhs)
                already_exists = True

        if not already_exists:
            equals_list.append([lhs, rhs])

    return equals_list


def construct_nor_inputs_rename_map(
    data: dict[str, Any], module: str
) -> dict[int, int]:
    equals_list = construct_nor_inputs_equals_list(data, module)

    rename_map: dict[int, int] = {}

    for equals_entry in equals_list:
        rename_to = min(equals_entry)

        for rename_from in equals_entry:
            rename_map[rename_from] = rename_to

    return rename_map


def net_id_list_to_renamed_set(nets: list[int], rename_map: dict[int, int]) -> set[int]:
    out = set()

    for net_id in nets:
        out.add(rename_map.get(net_id, net_id))

    return out


def extract_nets_from_yosys_cell(
    yosys_type: str, yosys_connection: dict[str, Any], rename_map: dict[int, int]
) -> tuple[set[int], set[int], set[int]]:
    input_nets = []
    output_nets = []
    clk_nets = []

    try:
        if yosys_type == "DFF":
            input_nets = yosys_connection["D"]
            output_nets = yosys_connection["Q"]
            clk_nets = yosys_connection["C"]
        else:
            input_nets = yosys_connection["A"]
            output_nets = yosys_connection["Y"]
            if yosys_type == "NOR":
                input_nets.extend(yosys_connection["B"])
    except KeyError:
        log.error("Yosys netlist invalid format")
        raise

    return (
        net_id_list_to_renamed_set(input_nets, rename_map),
        net_id_list_to_renamed_set(clk_nets, rename_map),
        net_id_list_to_renamed_set(output_nets, rename_map),
    )


def yosys_to_minecraft_gates(
    data: dict[str, Any],
    module: str,
) -> tuple[list[MinecraftGate], dict[int, set[int]]]:
    gates: list[MinecraftGate] = []

    # Given a net id, what gates take this net as input or clk or output
    net_list: dict[int, set[int]] = {}
    rename_map = construct_nor_inputs_rename_map(data, module)

    def append_to_netlist(nets: set[int], gate_id: int) -> None:
        for net_id in nets:
            try:
                net_list[net_id].add(gate_id)
            except KeyError:
                net_list[net_id] = set([gate_id])

    for yosys_name, yosys_gate in data["modules"][module]["cells"].items():
        gate_id = len(gates)

        yosys_type = yosys_gate["type"]
        yosys_connection = yosys_gate["connections"]

        input_nets, clk_nets, output_nets = extract_nets_from_yosys_cell(
            yosys_type, yosys_connection, rename_map
        )

        append_to_netlist(input_nets, gate_id)
        append_to_netlist(clk_nets, gate_id)
        append_to_netlist(output_nets, gate_id)

        gates.append(
            MinecraftGate(
                name=yosys_name.split("$")[-1],
                gate_type=get_gate_type(yosys_type),
                inputs=input_nets,
                outputs=output_nets,
                clk_inputs=clk_nets,
            )
        )

    for port_name, yosys_port in data["modules"][module]["ports"].items():
        gate_id = len(gates)

        gate_type = get_gate_type(yosys_port["direction"])
        gate_nets = net_id_list_to_renamed_set(yosys_port["bits"], rename_map)

        append_to_netlist(gate_nets, gate_id)

        if gate_type == GateType.IN:
            gates.append(
                MinecraftGate(
                    name=port_name,
                    gate_type=gate_type,
                    inputs=set(),
                    outputs=gate_nets,
                    clk_inputs=set(),
                )
            )
        else:
            gates.append(
                MinecraftGate(
                    name=port_name,
                    gate_type=gate_type,
                    inputs=gate_nets,
                    outputs=set(),
                    clk_inputs=set(),
                )
            )

    return gates, net_list


def construct_reverse_netlist(netlist: dict[int, set[int]]) -> dict[int, set[int]]:
    reverse_netlist: dict[int, set[int]] = {}

    for net_id, gate_ids in netlist.items():
        for gate_id in gate_ids:
            try:
                reverse_netlist[gate_id].add(net_id)
            except KeyError:
                reverse_netlist[gate_id] = set([net_id])

    return reverse_netlist
