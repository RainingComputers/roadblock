from math import inf, exp
from random import random
from abc import ABC, abstractmethod

import matplotlib.pyplot as plt

from roadblock.grid import MinecraftGrid
from roadblock.dim import Dim
from roadblock import log


class Placer(ABC):
    def __init__(self) -> None:
        self._cost = inf
        self._best_cost = inf
        self._steps = 0
        self._swaps = 0

    @property
    @abstractmethod
    def hud_string(self) -> str:
        pass

    @abstractmethod
    def update(self, grid: MinecraftGrid) -> bool:
        pass

    def update_cost(
        self, new_cost: float, a: int, a_pos: Dim, b: int, b_pos: Dim
    ) -> None:
        self._swaps += 1
        self._cost = new_cost

        if new_cost < self._best_cost:
            self._best_cost = new_cost


class RandomPlacer(Placer):
    def __init__(self, max_steps: int) -> None:
        super().__init__()
        self._max_steps = max_steps

        self._graph_costs: list[float] = []

        log.info("Random placer initialized")

    def update(self, grid: MinecraftGrid) -> bool:
        if self._steps == self._max_steps - 1:
            log.info("Random placement complete")
            self.plot_graph()
            return True

        a, a_pos, b, b_pos = grid.mutate()
        new_cost = grid.cost

        if new_cost < self._cost:
            self.update_cost(new_cost, a, a_pos, b, b_pos)
        else:
            grid.undo_mutate(a, a_pos, b, b_pos)

        self._steps += 1

        self._graph_costs.append(self._cost)

        return False

    @property
    def hud_string(self) -> str:
        return f"cost={self._cost} swaps={self._swaps} steps={self._steps}"

    def plot_graph(self) -> None:
        log.info("Plotting performance graph")

        fig, ax = plt.subplots(1, 1, sharex=True, figsize=(8, 2))

        ax.plot(self._graph_costs)
        ax.set(ylabel="Cost")
        ax.grid(True)

        plt.show(block=False)


class AnnealingPlacer(Placer):
    def __init__(
        self,
        init_temp: float,
        min_temp: float,
        max_steps: int,
    ) -> None:
        super().__init__()
        self._max_steps = max_steps

        self._temp = init_temp
        self._init_temp = init_temp
        self._min_temp = min_temp
        self._d_temp = init_temp - min_temp

        self._accept_prob = 0.0

        self._graph_temps: list[float] = []
        self._graph_probs: list[float] = []
        self._graph_costs: list[float] = []

        log.info("Annealing placer initialized")

    def update(self, grid: MinecraftGrid) -> bool:
        if self._steps == self._max_steps - 1 or self._temp < self._min_temp:
            log.info("Annealing complete")
            self.plot_graph()
            return True

        a, a_pos, b, b_pos = grid.mutate()
        new_cost = grid.cost

        if new_cost < self._cost:
            self.update_cost(new_cost, a, a_pos, b, b_pos)
        else:
            d_cost = new_cost - self._cost
            self._accept_prob = exp(-d_cost / self._temp)

            if random() < self._accept_prob:
                self.update_cost(new_cost, a, a_pos, b, b_pos)
            else:
                grid.undo_mutate(a, a_pos, b, b_pos)

        # self.mue = 1 + ((new_cost - self.best_cost) / new_cost)
        # self.temp *= self.mue

        self._temp = self._min_temp + self._d_temp * (
            ((self._max_steps - self._steps) / self._max_steps) ** 2
        )

        self._steps += 1

        self.update_graph()
        return False

    @property
    def hud_string(self) -> str:
        return (
            f"cost={self._cost} best={self._best_cost} swaps={self._swaps}"
            + f" steps={self._steps} temp={round(self._temp, 3)}"
            + f" accept_prob={round(self._accept_prob*100)}%"
        )

    def update_graph(self) -> None:
        self._graph_costs.append(self._cost)
        self._graph_probs.append(self._accept_prob)
        self._graph_temps.append(self._temp)

    def plot_graph(self) -> None:
        log.info("Plotting performance graph")

        fig, [ax1, ax2, ax3] = plt.subplots(3, 1, sharex=True, figsize=(8, 6))

        ax1.plot(self._graph_costs)
        ax1.set(ylabel="Cost")
        ax1.grid(True)

        ax2.plot(self._graph_temps)
        ax2.set(ylabel="Temp")
        ax2.grid(True)

        ax3.plot(self._graph_probs)
        ax3.set(ylabel="Prob", xlabel="Steps")
        ax3.grid(True)

        plt.show(block=False)
