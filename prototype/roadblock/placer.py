import math

from roadblock.grid import MinecraftGrid

from roadblock import log


class RandomPlacer:
    def __init__(self) -> None:
        self.cost = math.inf
        self.steps = 0
        self.swaps = 0

    def update(self, grid: MinecraftGrid) -> None:
        a, a_pos, b, b_pos = grid.mutate()
        new_cost = grid.cost

        if new_cost < self.cost:
            self.cost = new_cost
            self.swaps += 1
            log.debug(f"Move gate {a} to {a_pos}")
            log.debug(f"Move gate {b} to {b_pos}")
        else:
            grid.undo_mutate(a, a_pos, b, b_pos)

        self.steps += 1
