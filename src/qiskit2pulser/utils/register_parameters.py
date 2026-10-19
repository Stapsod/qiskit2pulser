import numpy as np

from src.qiskit2pulser.utils.pulser_parameters import PulserParameters


class RegisterParameters:
    def __init__(self, params: PulserParameters) -> None:
        self.step = params.step
        self.max_radius = params.max_radius

        k = int(self.max_radius // self.step)
        axis = np.arange(-k, k + 1) * self.step
        xs, ys = np.meshgrid(axis, axis)
        grid = np.column_stack((xs.ravel(), ys.ravel()))

        inside = np.linalg.norm(grid, axis=1) <= self.max_radius

        self.points = grid[inside]
        self.nb_points = len(self.points)

    def coordinates(self, p: int) -> tuple[float, float]:
        x, y = self.points[p]
        return float(x), float(y)
