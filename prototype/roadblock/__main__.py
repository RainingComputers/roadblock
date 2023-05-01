import sys
import subprocess
import json

from roadblock.netlist import (
    yosys_to_minecraft_cells,
    construct_out_in_map,
    show_circuit,
)

lib_file = sys.argv[1]
verilog_file = sys.argv[2]

yosys_file_name = verilog_file + ".ys"
yosys_netlist_json_file_name = verilog_file + ".json"

yosys_script = f"""
# read design
read_verilog {verilog_file}
hierarchy -check

# high-level synthesis
proc; opt; fsm; opt; memory; opt

# low-level synthesis
techmap;

# map to target architecture
dfflibmap -liberty {lib_file}
abc -liberty {lib_file}

# split larger signals
splitnets -ports; opt

# write to json file
write_json {yosys_netlist_json_file_name}

# show netlist
show
"""

print("🤖 Generating yosys script...")
with open(yosys_file_name, "w") as f:
    f.write(yosys_script)

print("🤖 Running yosys synthesis...")
subprocess.run(["yosys", yosys_file_name], check=True)
with open(yosys_netlist_json_file_name) as f:
    yosys_netlist = json.load(f)

print("🤖 Converting yosys netlist to minecraft netlist...")
cells, net_list = yosys_to_minecraft_cells(yosys_netlist)
out_in_map = construct_out_in_map(cells, net_list)
show_circuit(out_in_map, cells)
