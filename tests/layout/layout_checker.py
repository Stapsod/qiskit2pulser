import math
from dataclasses import dataclass, field

from qiskit2pulser.layout.layout import Layout
from qiskit2pulser.parameters.layout_parameters import LayoutParameters

# Tolerance used when comparing two float computations of the same quantity
REL_TOL = 1e-9
ABS_TOL = 1e-12


@dataclass
class LayoutChecker:
    params: LayoutParameters
    layout: Layout = field(init=False)
    points: list[tuple[float, float]] = field(init=False)

    def __post_init__(self):
        self.layout = Layout(self.params)
        self.points = [self.layout.coordinates(p) for p in range(self.layout.nb_points)]

    def _expected_grid(self) -> set[tuple[float, float]]:
        """Every lattice point inside the disk, enumerated independently."""
        step, radius = self.params.step, self.params.max_radius
        k = math.ceil(radius / step) + 1  # deliberately generous bound
        return {
            (i * step, j * step)
            for i in range(-k, k + 1)
            for j in range(-k, k + 1)
            if math.hypot(i * step, j * step) <= radius
        }

    def check_nb_points(self):
        assert self.layout.nb_points == len(self.points) == len(self.layout.cells), (
            "LayoutChecker.check_nb_points: nb_points does not match the number of cells"
        )

    def check_grid_correctness(self):
        step, radius = self.params.step, self.params.max_radius
        for p, (x, y) in enumerate(self.points):
            for c in (x, y):
                assert math.isclose(
                    c / step, round(c / step), rel_tol=REL_TOL, abs_tol=ABS_TOL
                ), (
                    f"LayoutChecker.check_grid_correctness: location {p} at {(x, y)} is not on the grid of step {step}"
                )
            assert math.hypot(x, y) <= radius, (
                f"LayoutChecker.check_grid_correctness: location {p} at {(x, y)} is outside the disk of radius {radius}"
            )
        assert len(set(self.points)) == len(self.points), (
            "LayoutChecker.check_grid_correctness: some locations are duplicated"
        )

    def check_grid_completeness(self):
        expected = self._expected_grid()
        missing = expected - set(self.points)
        assert not missing, (
            f"LayoutChecker.check_grid_completeness: {len(missing)} lattice points inside the disk are missing, e.g. {sorted(missing)[:5]}"
        )

    def check_distance(self):
        n = self.layout.nb_points
        for p in range(n):
            assert self.layout.distance(p, p) == 0, (
                f"LayoutChecker.check_distance: distance({p}, {p}) is not 0"
            )
            for q in range(p + 1, n):
                d = self.layout.distance(p, q)
                expected = math.dist(self.points[p], self.points[q])
                assert math.isclose(d, expected, rel_tol=REL_TOL, abs_tol=ABS_TOL), (
                    f"LayoutChecker.check_distance: distance({p}, {q}) = {d}, expected {expected}"
                )
                assert d == self.layout.distance(q, p), (
                    f"LayoutChecker.check_distance: distance is not symmetric for ({p}, {q})"
                )
