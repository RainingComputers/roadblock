from typing import Any
import dataclasses
from enum import Enum
from graphviz import Graph

from roadblock.dim import Dim

GateType = Enum("GateType", ["BUFF", "NOT", "DFF", "IN", "OUT"])


@dataclasses.dataclass
class MinecraftGate:
    name: str
    gate_type: GateType
    inputs: list[int] | None
    outputs: list[int] | None
    clk_inputs: list[int] | None

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
        return Dim(0, 0)

    @property
    def out_coords(self) -> Dim:
        if self.gate_type == GateType.NOT:
            return Dim(0, 1)

        return Dim(0, 0)

    @property
    def is_port(self) -> bool:
        return self.gate_type == GateType.IN or self.gate_type == GateType.OUT


def get_gate_type(yosys_type: dict[str, Any]) -> GateType:
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

    raise KeyError


def yosys_to_minecraft_gates(
    data: dict[str, Any],
) -> tuple[list[MinecraftGate], dict[int, set[int]]]:
    gates: list[MinecraftGate] = []

    # Given a gate id, what gates take this net as input or clk
    net_list: dict[int, set[int]] = {}

    def append_to_netlist(nets: list[int], gate_id: int) -> None:
        for net in nets:
            try:
                net_list[net].add(gate_id)
            except KeyError:
                net_list[net] = set([gate_id])

    for yosys_name, yosys_gate in data["modules"]["adder"]["cells"].items():
        gate_id = len(gates)

        yosys_type = yosys_gate["type"]
        yosys_connection = yosys_gate["connections"]

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

        append_to_netlist(input_nets, gate_id)
        if clk_nets is not None:
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

    for port_name, yosys_port in data["modules"]["adder"]["ports"].items():
        gate_id = len(gates)

        port_nets = yosys_port["bits"]
        port_type = get_gate_type(yosys_port["direction"])

        if port_type == GateType.IN:
            gates.append(
                MinecraftGate(
                    name=port_name,
                    gate_type=port_type,
                    inputs=None,
                    outputs=port_nets,
                    clk_inputs=None,
                )
            )
        else:
            append_to_netlist(port_nets, gate_id)

            gates.append(
                MinecraftGate(
                    name=port_name,
                    gate_type=port_type,
                    inputs=port_nets,
                    outputs=None,
                    clk_inputs=None,
                )
            )

    return gates, net_list


def construct_out_in_map(
    gates: list[MinecraftGate], net_list: dict[int, set[int]]
) -> dict[int, set[int]]:
    # Given a gate, what other gates take its output as input or clock
    out_in_map: dict[int, set[int]] = {}

    for gate_id, gate in enumerate(gates):
        if gate.outputs is None:
            continue

        for out_net in gate.outputs:
            try:
                out_in_map[gate_id] = net_list[out_net]
            except KeyError:
                print(
                    f"WARN: Inputs not found for {gate.name} net {out_net}",
                )

    return out_in_map


def show_circuit(
    gates: list[MinecraftGate],
    out_in_map: dict[int, set[int]],
) -> None:
    g = Graph()

    for out_gate, in_gates in out_in_map.items():
        for in_gate in in_gates:
            g.edge(gates[out_gate].full_name, gates[in_gate].full_name)

    g.view()
