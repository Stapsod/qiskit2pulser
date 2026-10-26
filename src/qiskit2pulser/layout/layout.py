import math

from qiskit2pulser.parameters.pulser_parameters import PulserParameters


class Layout:
    def __init__(self, params: PulserParameters) -> None:
        self.step = params.step
        self.max_radius = params.max_radius
        self.min_dist = params.min_dist
        self.threshold = params.threshold

        # Location p is the grid cell (i, j), at (i * step, j * step) µm
        k = int(self.max_radius // self.step)
        self.cells = [
            (i, j)
            for j in range(-k, k + 1)
            for i in range(-k, k + 1)
            if math.hypot(i * self.step, j * self.step) <= self.max_radius
        ]
        self.nb_points = len(self.cells)
        self._index = {cell: p for p, cell in enumerate(self.cells)}

        # The grid is regular: the neighbours are the same offsets everywhere
        r = int(self.threshold // self.step)
        too_close, cz = [], []
        for di in range(-r, r + 1):
            for dj in range(-r, r + 1):
                d = self.step * math.hypot(di, dj)
                if 0 < d < self.min_dist:
                    too_close.append((di, dj))
                elif self.min_dist <= d <= self.threshold:
                    cz.append((di, dj))

        self._too_close = [self._shift(p, too_close) for p in range(self.nb_points)]
        self._cz = [self._shift(p, cz) for p in range(self.nb_points)]

    def _shift(self, p: int, offsets: list[tuple[int, int]]) -> list[int]:
        i, j = self.cells[p]
        shifted = [(i + di, j + dj) for di, dj in offsets]
        return [self._index[c] for c in shifted if c in self._index]

    def coordinates(self, p: int) -> tuple[float, float]:
        i, j = self.cells[p]
        return i * self.step, j * self.step

    def distance(self, p: int, q: int) -> float:
        (i, j), (k, l) = self.cells[p], self.cells[q]
        return self.step * math.hypot(i - k, j - l)

    def too_close(self, p: int, q: int) -> bool:
        return 0 < self.distance(p, q) < self.min_dist

    def in_cz_range(self, p: int, q: int) -> bool:
        return self.min_dist <= self.distance(p, q) <= self.threshold

    def too_close_neighbours(self, p: int) -> list[int]:
        return self._too_close[p]

    def cz_neighbours(self, p: int) -> list[int]:
        """N(p)"""
        return self._cz[p]

    def too_close_pairs(self) -> list[tuple[int, int]]:
        """D, each pair once (p < q)"""
        return [
            (p, q) for p in range(self.nb_points) for q in self._too_close[p] if p < q
        ]

    def convert_to_pulser(self):
        pass
