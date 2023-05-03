import pygame
import numpy as np

from roadblock.placer import MinecraftGrid


def np2surf(arr: np.ndarray, scale: tuple[int, int]) -> pygame.Surface:
    im = (arr != -1) * 255

    surf = pygame.surfarray.make_surface(im)
    surf = pygame.transform.scale(surf, scale)

    return surf


def draw_grid(
    display: pygame.Surface, grid: MinecraftGrid, scale: tuple[int, int]
) -> None:
    grid_surf = np2surf(
        grid.grid,
        (
            grid.dim.x * scale[0],
            grid.dim.y * scale[1],
        ),
    )
    display.blit(grid_surf, (0, 0))

    pass
