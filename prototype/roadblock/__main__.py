import sys

import pygame

from roadblock.yosys import run_yosys_flow
from roadblock.dim import Dim
from roadblock.placer import AnnealingPlacer

from roadblock.router import route
from roadblock.grid import GatesGrid

from roadblock import visual
from roadblock import hud
from roadblock import log


log.enable_debug()

#  python3 -m roadblock roadblock_cells.lib test.v adder 16

lib_file = sys.argv[1]
verilog_file = sys.argv[2]
module = sys.argv[3]
grid_dim = Dim(int(sys.argv[4]), int(sys.argv[4]))
screen_dim = Dim(1024, 1024)
scale = screen_dim // grid_dim

pygame.init()
pygame.display.set_caption("Roadblock")
display = pygame.display.set_mode((screen_dim.x, screen_dim.y))

running = True
error = False
placement_complete = False  # TODO: Use an enum
routing_complete = False
placer = None
grid = None

while running:
    if error:
        hud.draw_logs(display, screen_dim)
        pygame.display.update()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        continue

    try:
        if placer is None:
            gates, netlist = run_yosys_flow(verilog_file, lib_file, module)
            placer = AnnealingPlacer(
                init_temp=10,
                min_temp=0,
                max_steps=5000,
            )
            # placer = RandomPlacer(max_steps=2000)

            grid = GatesGrid(grid_dim, gates, netlist)
            log.info(
                f"{grid.num_filled} of {grid_dim.x*grid_dim.y} cells filled",
            )
        else:
            if not placement_complete:
                placement_complete = placer.update(grid)

        if placement_complete and not routing_complete and grid is not None:
            route(grid, 30)
            routing_complete = True

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            if event.type == pygame.MOUSEMOTION:
                pos = Dim(event.pos[0], event.pos[1])
                hud.update(grid, scale, pos)

        visual.draw_grid(display, grid, scale)
        hud.draw_hud(grid, display, placer, screen_dim, scale)

    except (ValueError, KeyError):
        error = True
        raise

    hud.draw_logs(display, screen_dim)
    pygame.display.update()
