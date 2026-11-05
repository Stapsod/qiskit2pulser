import pytest

from qiskit2pulser.parameters.layout_parameters import LayoutParameters
from tests.solvers.conftest import KNOWN_CASES, build_circuit
from tests.solvers.solver_checker import SolverChecker


def test_solution_shape(solver_checker: SolverChecker):
    solver_checker.check_solution_shape()


def test_distinct_locations(solver_checker: SolverChecker):
    solver_checker.check_distinct_locations()


def test_min_distance(solver_checker: SolverChecker):
    solver_checker.check_min_distance()


def test_cz_range(solver_checker: SolverChecker):
    solver_checker.check_cz_range()


@pytest.mark.parametrize(("nb_qubits", "cz", "params", "expected"), KNOWN_CASES)
def test_expected_answer(nb_qubits, cz, params, expected):
    checker = SolverChecker(build_circuit(nb_qubits, cz), LayoutParameters(*params))
    assert checker.is_sat == expected, (
        f"expected {'SAT' if expected else 'UNSAT'}, got {'SAT' if checker.is_sat else 'UNSAT'}"
    )
