import sys

import pygame

from roadblock.yosys import run_yosys_flow
from roadblock.dim import Dim
from roadblock.placer import AnnealingPlacer
from roadblock.grid import MinecraftGrid

from roadblock import visual
from roadblock import hud
from roadblock import log


log.enable_debug()

lib_file = sys.argv[1]
verilog_file = sys.argv[2]
module = "adder"
grid_dim = Dim(16, 16)
screen_dim = Dim(1024, 1024)
scale = screen_dim // grid_dim

pygame.init()
pygame.display.set_caption("Roadblock")
display = pygame.display.set_mode((screen_dim.x, screen_dim.y))

running = True
error = False
complete = False
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
            gates, out_in_map = run_yosys_flow(verilog_file, lib_file, module)
            placer = AnnealingPlacer(
                init_temp=10,
                min_temp=0,
                max_steps=5000,
            )
            # placer = RandomPlacer(max_steps=2000)

            grid = MinecraftGrid(grid_dim, gates, out_in_map)
            log.info(
                f"{grid.num_filled} of {grid_dim.x*grid_dim.y} cells filled",
            )
        else:
            if not complete:
                complete = placer.update(grid)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            if event.type == pygame.MOUSEMOTION:
                pos = Dim(event.pos[0], event.pos[1])
                hud.update(grid, scale, pos)

        visual.draw_grid(display, grid, scale)
        hud.draw_hud(grid, display, placer, screen_dim, scale)

    except ValueError:
        error = True

    hud.draw_logs(display, screen_dim)
    pygame.display.update()
