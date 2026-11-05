import random

import pytest

from qiskit2pulser.parameters.layout_parameters import LayoutParameters
from tests.layout.layout_checker import LayoutChecker

# (step, max_radius, min_dist, threshold)
EDGE_CASES = [
    (2, 50, 4, 6.6),  # DigitalAnalogDevice, step 2 (P = 1961)
    (4, 50, 4, 6.6),  # DigitalAnalogDevice, step 4 (P = 489)
    (5, 3, 4, 6.6),  # Radius smaller than step: a single location
    (1, 6, 4, 4),  # threshold == min_dist
    (3, 10, 2, 6),  # min_dist < step: no too-close neighbour
    (1.5, 8, 4, 6.6),  # step does not divide min_dist
    (0.1, 0.5, 0.3, 0.3),  # Float step, boundaries on exact multiples
    (0.3, 3, 0.9, 1.2),  # Float step, boundaries on exact multiples
]


def random_case(seed: int) -> tuple[float, float, float, float]:
    # Values rounded to 0.1 so that distances often land exactly on a boundary
    rng = random.Random(f"layout-{seed}")
    step = round(rng.uniform(0.5, 4), 1)
    max_radius = round(rng.uniform(step, 10 * step), 1)  # keeps P small
    min_dist = round(rng.uniform(0.5, 6), 1)
    threshold = round(min_dist + rng.uniform(0, 4), 1)
    return step, max_radius, min_dist, threshold


CASES = EDGE_CASES + [random_case(s) for s in range(30)]


def case_id(case: tuple[float, float, float, float]) -> str:
    step, max_radius, min_dist, threshold = case
    return f"s{step}-r{max_radius}-m{min_dist}-t{threshold}"


@pytest.fixture(scope="module", params=CASES, ids=case_id)
def layout_checker(request) -> LayoutChecker:
    return LayoutChecker(LayoutParameters(*request.param))
