from math import inf, exp
from random import random
from abc import ABC, abstractmethod

import matplotlib.pyplot as plt

from roadblock.grid import MinecraftGrid
from roadblock import log


class Placer(ABC):
    @property
    @abstractmethod
    def hud_string(self) -> str:
        pass

    @abstractmethod
    def update(self, grid: MinecraftGrid) -> bool:
        pass


class RandomPlacer(Placer):
    def __init__(self, max_steps: int) -> None:
        self.cost = inf
        self.steps = 0
        self.max_steps = max_steps
        self.swaps = 0
        log.info("Random placer initialized")

        self.costs: list[float] = []

    @property
    def hud_string(self) -> str:
        return f"cost={self.cost} swaps={self.swaps} steps={self.steps}"

    def plot_graph(self) -> None:
        log.info("Plotting performance graph")

        fig, ax = plt.subplots(1, 1, sharex=True, figsize=(8, 2))

        ax.plot(self.costs)
        ax.set(ylabel="Cost")
        ax.grid(True)

        plt.show()

    def update(self, grid: MinecraftGrid) -> bool:
        if self.steps == self.max_steps - 1:
            log.info("Random placement complete")
            self.plot_graph()
            return True

        a, a_pos, b, b_pos = grid.mutate()
        new_cost = grid.cost

        if new_cost < self.cost:
            self.cost = new_cost
            self.swaps += 1
            log.debug(f"Move gate {a} from old pos {a_pos}")
            log.debug(f"Move gate {b} from old pos {b_pos}")
        else:
            grid.undo_mutate(a, a_pos, b, b_pos)

        self.steps += 1

        self.costs.append(self.cost)

        return False


class AnnealingPlacer(Placer):
    def __init__(
        self,
        init_temp: float,
        min_temp: float,
        max_steps: int,
    ) -> None:
        self.cost = inf
        self.best_cost = inf
        self.max_steps = max_steps

        self.temp = init_temp
        self.init_temp = init_temp
        self.min_temp = min_temp
        self.delta_temp = init_temp - min_temp

        self.steps = 0
        self.swaps = 0
        self.accept_prob = 0.0
        log.info("Annealing placer initialized")

        self.temps: list[float] = []
        self.probs: list[float] = []
        self.costs: list[float] = []

    @property
    def hud_string(self) -> str:
        return (
            f"cost={self.cost} best={self.best_cost} swaps={self.swaps}"
            + f" steps={self.steps} accept_prob={round(self.accept_prob, 3)}"
            + f" temp={round(self.temp, 3)}"
        )

    def plot_graph(self) -> None:
        log.info("Plotting performance graph")

        fig, [ax1, ax2, ax3] = plt.subplots(3, 1, sharex=True, figsize=(8, 6))

        ax1.plot(self.costs)
        ax1.set(ylabel="Cost")
        ax1.grid(True)

        ax2.plot(self.temps)
        ax2.set(ylabel="Temp")
        ax2.grid(True)

        ax3.plot(self.probs)
        ax3.set(ylabel="Prob", xlabel="Steps")
        ax3.grid(True)

        plt.show()

    def update(self, grid: MinecraftGrid) -> bool:
        if self.steps == self.max_steps - 1 or self.temp < self.min_temp:
            log.info("Annealing complete")
            self.plot_graph()
            return True

        a, a_pos, b, b_pos = grid.mutate()
        new_cost = grid.cost

        if new_cost < self.cost:
            self.cost = new_cost
            self.swaps += 1
            log.debug(f"Move gate {a} from old pos {a_pos}")
            log.debug(f"Move gate {b} from old pos {b_pos}")
        else:
            delta_cost = new_cost - self.cost
            self.accept_prob = exp(-delta_cost / self.temp)

            if random() < self.accept_prob:
                self.cost = new_cost
                self.swaps += 1
            else:
                grid.undo_mutate(a, a_pos, b, b_pos)

        if new_cost < self.best_cost:
            self.best_cost = new_cost

        # self.mue = 1 + ((new_cost - self.best_cost) / new_cost)
        # self.temp *= self.mue

        self.temp = self.min_temp + (
            self.delta_temp * ((self.max_steps - self.steps) / self.max_steps)
        )

        self.steps += 1

        self.costs.append(self.cost)
        self.probs.append(self.accept_prob)
        self.temps.append(self.temp)

        return False
