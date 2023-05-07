import sys

import pygame

from roadblock.yosys import run_yosys_flow
from roadblock.dim import Dim
from roadblock.placer import RandomPlacer
from roadblock.grid import MinecraftGrid

from roadblock import visual
from roadblock import hud


lib_file = sys.argv[1]
verilog_file = sys.argv[2]
grid_dim = Dim(64, 64)
screen_dim = Dim(1024, 1024)

# TODO: op overloading
scale = Dim(screen_dim.x // grid_dim.x, screen_dim.y // grid_dim.y)

pygame.init()
pygame.display.set_caption("Roadblock")
display = pygame.display.set_mode((screen_dim.x, screen_dim.y))

running = True
placer = None
grid = None

while running:
    if placer is None:
        gates, out_in_map = run_yosys_flow(verilog_file, lib_file)
        placer = RandomPlacer()
        grid = MinecraftGrid(grid_dim, gates, out_in_map)
    else:
        placer.update(grid)

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        if event.type == pygame.MOUSEMOTION:
            pos = Dim(event.pos[0], event.pos[1])
            hud.update(grid, scale, pos)

    visual.draw_grid(display, grid, scale)
    hud.draw_hud(grid, display, placer, screen_dim, scale)

    pygame.display.update()
