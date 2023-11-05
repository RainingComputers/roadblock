import pygame
import numpy as np

from roadblock.dim import Dim
from roadblock.grid import GatesGrid

colors = None


def get_colors(num_gates: int) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    global colors

    if colors is not None:
        return colors

    colors = (
        np.random.randint(100, 256, num_gates),
        np.random.randint(100, 256, num_gates),
        np.random.randint(100, 256, num_gates),
    )

    return colors


def grid_to_surface(
    arr: np.ndarray,
    scale: Dim,
    colors: tuple[np.ndarray, np.ndarray, np.ndarray],
) -> pygame.Surface:
    r_vals, g_vals, b_vals = colors
    r_grid = np.where(arr == -1, 0, r_vals[arr])
    g_grid = np.where(arr == -1, 0, g_vals[arr])
    b_grid = np.where(arr == -1, 0, b_vals[arr])

    im = np.dstack((r_grid, g_grid, b_grid))

    surf = pygame.surfarray.make_surface(im)
    surf = pygame.transform.scale(surf, (scale.x, scale.y))

    return surf


def draw_grid(
    display: pygame.Surface,
    grid: GatesGrid,
    scale: Dim,
) -> None:
    colors = get_colors(grid.num_gates)

    grid_surf = grid_to_surface(
        grid._grid,
        grid.dim * scale,
        colors,
    )
    display.blit(grid_surf, (0, 0))

    pass
