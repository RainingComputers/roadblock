import subprocess
import json

from roadblock.netlist import (
    yosys_to_minecraft_gates,
    construct_out_in_map,
    show_circuit,
    MinecraftGate,
)

from roadblock import log


def get_yosys_script(
    verilog_file: str,
    lib_file: str,
    yosys_netlist_json_file_name: str,
) -> str:
    yosys_script = f"""
# read design
read_verilog {verilog_file}
hierarchy -check

# high-level synthesis
proc; opt; fsm; opt; memory; opt

# low-level synthesis
techmap; opt

# map to target architecture
dfflibmap -liberty {lib_file}
abc -liberty {lib_file}

# split larger signals
splitnets -ports; opt

# write to json file
write_json {yosys_netlist_json_file_name}
"""

    return yosys_script


def run_yosys_flow(
    verilog_file: str, lib_file: str
) -> tuple[list[MinecraftGate], dict[int, set[int]]]:
    yosys_file_name = verilog_file + ".ys"
    yosys_netlist_json_file_name = verilog_file + ".json"

    log.info("Generating yosys script")
    with open(yosys_file_name, "w") as f:
        f.write(
            get_yosys_script(
                verilog_file,
                lib_file,
                yosys_netlist_json_file_name,
            )
        )

    log.info("Running yosys synthesis")
    subprocess.run(["yosys", yosys_file_name], check=True)
    with open(yosys_netlist_json_file_name) as f:
        yosys_netlist = json.load(f)

    log.info("Converting yosys netlist to minecraft netlist")
    gates, net_list = yosys_to_minecraft_gates(yosys_netlist)
    out_in_map = construct_out_in_map(gates, net_list)

    log.info(f"Result is {len(gates)} gates")

    show_circuit(gates, out_in_map)

    return gates, out_in_map
