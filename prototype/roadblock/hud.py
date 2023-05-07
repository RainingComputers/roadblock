import pygame

from roadblock.placer import RandomPlacer
from roadblock.grid import MinecraftGrid
from roadblock.dim import Dim

from roadblock import log


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


def render_text(text: str, color: str = "white") -> pygame.Surface:
    font = pygame.font.SysFont("courier", FONT_SIZE, bold=1)
    font_surf = font.render(
        " " + text,
        True,
        pygame.Color(color),
        pygame.Color("black"),
    )
    font_surf.set_alpha(FONT_ALPHA)

    return font_surf


gate_name = ""

select_gate_id = None

FONT_SIZE = 18
FONT_ALPHA = 180
LOG_LENGTH = 20


def update(grid: MinecraftGrid, scale: Dim, pos: Dim) -> None:
    global gate_name
    global select_gate_id

    gate_name, select_gate_id = get_gate(grid, scale, pos)


def draw_placer_stats(
    placer: RandomPlacer,
    display: pygame.Surface,
    screen_dim: Dim,
) -> None:
    name_text = render_text(gate_name)
    cost_text = render_text(
        f"cost={placer.cost} swaps={placer.swaps} steps={placer.steps}"
    )

    display.blit(cost_text, (0, 10))
    display.blit(name_text, (0, 10 + FONT_SIZE))


def draw_logs(display: pygame.Surface, screen_dim: Dim) -> None:
    logs = log.logs[-LOG_LENGTH:]

    info_text = render_text(" [INFO]", "green")
    warn_text = render_text(" [WARN]", "yellow")
    error_text = render_text("[ERROR]", "red")

    level_text_dict = {
        log.LogLevel.INFO: info_text,
        log.LogLevel.WARN: warn_text,
        log.LogLevel.ERROR: error_text,
    }

    for i, log_item in enumerate(logs):
        rev_i = LOG_LENGTH - i
        y = screen_dim.y - FONT_SIZE * 2 - rev_i * FONT_SIZE

        display.blit(
            level_text_dict[log_item.level],
            (0, y),
        )

        message_text = render_text(log_item.message)

        display.blit(message_text, (5 * FONT_SIZE - 2, y))


def draw_hud(
    grid: MinecraftGrid,
    display: pygame.Surface,
    placer: RandomPlacer,
    screen_dim: Dim,
    scale: Dim,
) -> None:
    draw_select_rectangle(display, grid, scale, select_gate_id)
    draw_placer_stats(placer, display, screen_dim)
