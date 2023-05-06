import sys
import subprocess
import json
import pygame

from roadblock.netlist import (
    yosys_to_minecraft_gates,
    construct_out_in_map,
    show_circuit,
)

from roadblock.placer import MinecraftGrid, RandomPlacer
from roadblock.visual import draw_grid, get_gate, draw_select_rectangle

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

print("INFO: 🤖 Generating yosys script")
with open(yosys_file_name, "w") as f:
    f.write(yosys_script)

print("INFO: 🤖 Running yosys synthesis")
subprocess.run(["yosys", yosys_file_name], check=True)
with open(yosys_netlist_json_file_name) as f:
    yosys_netlist = json.load(f)

print("INFO: 🤖 Converting yosys netlist to minecraft netlist")
gates, net_list = yosys_to_minecraft_gates(yosys_netlist)
out_in_map = construct_out_in_map(gates, net_list)
print(f"INFO: 🤖 Result is {len(gates)} gates")

show_circuit(out_in_map, gates)

grid_dim = Dim(32, 32)
screen_dim = (512, 512)
scale = (screen_dim[0] // grid_dim.x, screen_dim[1] // grid_dim.y)

grid = MinecraftGrid(grid_dim, gates, out_in_map)
placer = RandomPlacer()

running = True
pygame.init()
infoObject = pygame.display.Info()
display = pygame.display.set_mode(screen_dim)
pygame.display.set_caption("Roadblock place and route")
font = pygame.font.SysFont("courier", 24, bold=1)

gate_name = ""
select_gate_id = None
cost = placer.cost

while running:
    cost = placer.update(grid)

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        if event.type == pygame.MOUSEMOTION:
            gate_name, select_gate_id = get_gate(grid, scale, event.pos)

    draw_grid(display, grid, scale)

    draw_select_rectangle(display, grid, scale, select_gate_id)

    name_text = font.render(
        gate_name, True, pygame.Color("white"), pygame.Color("black")
    )

    cost_text = font.render(
        f"cost={str(cost)}", True, pygame.Color("white"), pygame.Color("black")
    )

    display.blit(name_text, (10, 10))
    display.blit(cost_text, (10, screen_dim[1] - 40))

    pygame.display.update()
