import pygame

from roadblock.placer import Placer
from roadblock.grid import MinecraftGrid
from roadblock.dim import Dim

from roadblock import log


def render_text(text: str, color: str = "white") -> pygame.Surface:
    font = pygame.font.SysFont("courier", FONT_SIZE, bold=1)
    font_surf = font.render(
        " " + text + " ",
        True,
        pygame.Color(color),
        pygame.Color("black"),
    )
    font_surf.set_alpha(FONT_ALPHA)

    return font_surf


def get_gate(
    grid: MinecraftGrid,
    scale: Dim,
    pos: Dim,
) -> tuple[str, int | None]:
    gate_pos = pos // scale

    gate_id = grid.get_gate_id_from_pos(gate_pos)

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
gate_pos = None

FONT_SIZE = 18
FONT_ALPHA = 180
LOG_LENGTH = 20


def update(grid: MinecraftGrid, scale: Dim, pos: Dim) -> None:
    global gate_name
    global select_gate_id
    global gate_pos

    gate_pos = pos
    gate_name, select_gate_id = get_gate(grid, scale, pos)


def draw_placer_stats(
    placer: Placer,
    display: pygame.Surface,
    screen_dim: Dim,
) -> None:
    if gate_name != "":
        name_text = render_text(gate_name)
        display.blit(name_text, (0, 10 + FONT_SIZE))

    if gate_pos is not None:
        pos_text = render_text(str(gate_pos))
        display.blit(pos_text, (0, 10 + 2 * FONT_SIZE))

    cost_text = render_text(placer.hud_string)
    display.blit(cost_text, (0, 10))


def draw_logs(display: pygame.Surface, screen_dim: Dim) -> None:
    logs = log.logs[-LOG_LENGTH:]

    info_text = render_text(" [INFO]", "green")
    warn_text = render_text(" [WARN]", "yellow")
    error_text = render_text("[ERROR]", "red")
    debug_text = render_text("[DEBUG]", "cyan")

    level_text_dict = {
        log.LogLevel.INFO: info_text,
        log.LogLevel.WARN: warn_text,
        log.LogLevel.ERROR: error_text,
        log.LogLevel.DEBUG: debug_text,
    }

    for i, log_item in enumerate(logs):
        rev_i = len(logs) - i
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
    placer: Placer,
    screen_dim: Dim,
    scale: Dim,
) -> None:
    draw_select_rectangle(display, grid, scale, select_gate_id)
    draw_placer_stats(placer, display, screen_dim)
