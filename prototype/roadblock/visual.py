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
