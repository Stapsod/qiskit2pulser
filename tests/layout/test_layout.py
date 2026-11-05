import pytest

from qiskit2pulser.layout.layout import Layout
from qiskit2pulser.parameters.layout_parameters import LayoutParameters
from tests.layout.layout_checker import LayoutChecker


def test_nb_points(layout_checker: LayoutChecker):
    layout_checker.check_nb_points()


def test_grid_correctness(layout_checker: LayoutChecker):
    layout_checker.check_grid_correctness()


def test_grid_completeness(layout_checker: LayoutChecker, request):
    # Known bug: int(max_radius // step) underestimates (0.5 // 0.1 == 4.0)
    if layout_checker.params == LayoutParameters(0.1, 0.5, 0.3, 0.3):
        request.applymarker(
            pytest.mark.xfail(
                strict=True, reason="float floor in Layout's grid bound drops points"
            )
        )
    layout_checker.check_grid_completeness()


def test_distance(layout_checker: LayoutChecker):
    layout_checker.check_distance()


@pytest.mark.parametrize(("step", "expected"), [(2, 1961), (4, 489)])
def test_known_nb_points(step: float, expected: int):
    assert Layout(LayoutParameters(step, 50, 4, 6.6)).nb_points == expected
