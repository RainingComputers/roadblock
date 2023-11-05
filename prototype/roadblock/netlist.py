from typing import Any
from dataclasses import dataclass
from enum import Enum
from graphviz import Graph

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


def extract_nets_from_yosys_cell(
    yosys_type: str, yosys_connection: dict[str, Any]
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

    return set(input_nets), set(clk_nets), set(output_nets)


def yosys_to_minecraft_gates(
    data: dict[str, Any],
    module: str,
) -> tuple[list[MinecraftGate], dict[int, set[int]]]:
    gates: list[MinecraftGate] = []

    # Given a net id, what gates take this net as input or clk
    net_list: dict[int, set[int]] = {}

    def append_to_netlist(nets: set[int], gate_id: int) -> None:
        for net in nets:
            try:
                net_list[net].add(gate_id)
            except KeyError:
                net_list[net] = set([gate_id])

    for yosys_name, yosys_gate in data["modules"][module]["cells"].items():
        gate_id = len(gates)

        yosys_type = yosys_gate["type"]
        yosys_connection = yosys_gate["connections"]

        input_nets, clk_nets, output_nets = extract_nets_from_yosys_cell(
            yosys_type, yosys_connection
        )

        append_to_netlist(input_nets, gate_id)
        append_to_netlist(clk_nets, gate_id)

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
        gate_nets = yosys_port["bits"]

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
            append_to_netlist(gate_nets, gate_id)

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


def construct_out_in_map(
    gates: list[MinecraftGate], net_list: dict[int, set[int]]
) -> dict[int, set[int]]:
    # Given a gate, what other gates take its output as input or clock
    out_in_map: dict[int, set[int]] = {}

    for gate_id, gate in enumerate(gates):
        inp_gates: set[int] = set()

        for out_net in gate.outputs:
            try:
                inp_gates = inp_gates.union(net_list[out_net])
            except KeyError:
                log.warn(f"Inputs not found for {gate.name} net {out_net}")

        out_in_map[gate_id] = inp_gates

    return out_in_map


def construct_in_out_map(
    out_in_map: dict[int, set[int]],
) -> dict[int, set[int]]:
    # What gates feed into the given gate
    in_out_map: dict[int, set[int]] = {}

    for out_gate_id, in_gate_ids in out_in_map.items():
        for in_gate_id in in_gate_ids:
            try:
                in_out_map[in_gate_id].add(out_gate_id)
            except KeyError:
                in_out_map[in_gate_id] = set([out_gate_id])

    return in_out_map


def show_circuit(
    gates: list[MinecraftGate],
    out_in_map: dict[int, set[int]],
) -> None:
    g = Graph()

    for src_gate, dest_gates in out_in_map.items():
        for in_gate in dest_gates:
            g.edge(gates[src_gate].full_name, gates[in_gate].full_name)

    g.view()
