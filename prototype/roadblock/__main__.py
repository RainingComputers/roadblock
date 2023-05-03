import sys
import subprocess
import json
import pygame

from roadblock.netlist import (
    yosys_to_minecraft_cells,
    construct_out_in_map,
    show_circuit,
)

from roadblock.placer import MinecraftGrid, RandomPlacer
from roadblock.visual import draw_grid

from roadblock.dim import Dim

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
techmap; opt

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
print(f"🤖 Result is {len(cells)} cells")

show_circuit(out_in_map, cells)


grid_dim = Dim(22, 22)
screen_dim = (1024, 1024)
scale_dim = (screen_dim[0] // grid_dim.x, screen_dim[1] // grid_dim.y)


grid = MinecraftGrid(grid_dim, cells, out_in_map)
placer = RandomPlacer()

running = True
pygame.init()
infoObject = pygame.display.Info()
display = pygame.display.set_mode(screen_dim)
pygame.display.set_caption("Roadblock place and route")


while running:
    draw_grid(display, grid, scale_dim)
    pygame.display.update()

    placer.update(grid)

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            running = False
