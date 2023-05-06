import pygame
import numpy as np

from roadblock.placer import MinecraftGrid


def grid_to_surface(
    arr: np.ndarray,
    scale: tuple[int, int],
    colors: tuple[np.ndarray, np.ndarray, np.ndarray],
) -> pygame.Surface:
    r_vals, g_vals, b_vals = colors
    r_grid = np.where(arr == -1, 0, r_vals[arr])
    g_grid = np.where(arr == -1, 0, g_vals[arr])
    b_grid = np.where(arr == -1, 0, b_vals[arr])

    im = np.dstack((r_grid, g_grid, b_grid))

    surf = pygame.surfarray.make_surface(im)
    surf = pygame.transform.scale(surf, scale)

    return surf


def draw_grid(
    display: pygame.Surface, grid: MinecraftGrid, scale: tuple[int, int]
) -> None:
    grid_surf = grid_to_surface(
        grid.grid,
        (
            grid.dim.x * scale[0],
            grid.dim.y * scale[1],
        ),
        grid.colors,
    )
    display.blit(grid_surf, (0, 0))

    pass


def get_gate(
    grid: MinecraftGrid,
    scale: tuple[int, int],
    pos: tuple[int, int],
) -> tuple[str, int | None]:
    x = pos[0] // scale[0]
    y = pos[1] // scale[1]

    if x >= grid.dim.x or x < 0 or y >= grid.dim.y or y < 0:
        return "", None

    gate_id = grid.grid[x][y]

    if gate_id >= len(grid.gates) or gate_id < 0:
        return "", None

    return grid.gates[gate_id].full_name, gate_id


def draw_select_rectangle(
    display: pygame.Surface,
    grid: MinecraftGrid,
    scale: tuple[int, int],
    gate_id: int | None,
) -> None:
    if gate_id is None:
        return

    pos = grid.gate_map[gate_id]

    if pos is None:
        return

    gate = grid.gates[gate_id]
    dim = gate.dim

    rect = (
        pos.x * scale[0],
        pos.y * scale[1],
        dim.x * scale[0],
        dim.y * scale[1],
    )

    pygame.draw.rect(display, pygame.Color("red"), rect, 2)
