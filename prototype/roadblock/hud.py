import pygame

from roadblock.placer import RandomPlacer
from roadblock.grid import MinecraftGrid
from roadblock.dim import Dim


def get_gate(
    grid: MinecraftGrid,
    scale: Dim,
    pos: Dim,
) -> tuple[str, int | None]:
    # TODO: Op overloading
    x = pos.x // scale.x
    y = pos.y // scale.y

    gate_id = grid.get_gate_from_pos(Dim(x, y))

    if gate_id is None:
        return "", None

    return grid.get_gate_from_id(gate_id).full_name, gate_id


def draw_select_rectangle(
    display: pygame.Surface,
    grid: MinecraftGrid,
    scale: Dim,
    gate_id: int | None,
) -> None:
    if gate_id is None:
        return

    pos = grid.get_pos(gate_id)

    if pos is None:
        return

    gate = grid.get_gate_from_id(gate_id)
    dim = gate.dim

    rect = (
        pos.x * scale.x,
        pos.y * scale.y,
        dim.x * scale.x,
        dim.y * scale.y,
    )

    pygame.draw.rect(display, pygame.Color("red"), rect, 2)


gate_name = ""
select_gate_id = None


def update(grid: MinecraftGrid, scale: Dim, pos: Dim) -> None:
    global gate_name
    global select_gate_id

    gate_name, select_gate_id = get_gate(grid, scale, pos)


def draw_placer_stats(
    placer: RandomPlacer,
    display: pygame.Surface,
    font: pygame.font.Font,
    screen_dim: Dim,
) -> None:
    name_text = font.render(
        gate_name, True, pygame.Color("white"), pygame.Color("black")
    )

    cost_text = font.render(
        f"cost={placer.cost} swaps={placer.swaps} steps={placer.steps}",
        True,
        pygame.Color("white"),
        pygame.Color("black"),
    )

    display.blit(name_text, (10, 10))
    display.blit(cost_text, (10, screen_dim.y - 40))


def draw_hud(
    grid: MinecraftGrid,
    display: pygame.Surface,
    placer: RandomPlacer,
    screen_dim: Dim,
    scale: Dim,
) -> None:
    font = pygame.font.SysFont("courier", 24, bold=1)

    draw_placer_stats(placer, display, font, screen_dim)
    draw_select_rectangle(display, grid, scale, select_gate_id)
