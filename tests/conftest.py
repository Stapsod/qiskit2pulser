import pytest

pytest.register_assert_rewrite("tests.DAG.dag_checker")

from src.qiskit2pulser.qiskit_to_dag import _gate_types  # noqa: E402
from tests.circuit_generator import generate_circuit_and_dag  # noqa: E402
from tests.DAG.dag_checker import DAGChecker  # noqa: E402


@pytest.fixture(scope="module", params=range(50), ids=lambda s: f"seed{s}")
def checker(request) -> DAGChecker:
    return DAGChecker(
        *generate_circuit_and_dag(4, 5, list(_gate_types.keys()), request.param)
    )
