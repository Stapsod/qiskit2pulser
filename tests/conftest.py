import pytest

pytest.register_assert_rewrite("tests.DAG.dag_checker")

import random

from qiskit2pulser.DAG.qiskit_to_dag import _gate_types
from tests.circuit_generator import generate_circuit_and_dag
from tests.DAG.dag_checker import DAGChecker


def random_case(seed: int) -> tuple[int, int, int]:
    rng = random.Random(f"size-{seed}")
    return (seed, rng.randint(1, 8), rng.randint(0, 50))


EDGE_CASES = [
    (0, 0),  # No qubit
    (4, 0),  # Empty circuit
    (1, 20),  # Single-qubit gates only
    (8, 3),  # More qubits than gates
    (2, 50),  # Many cz on 2 qubits
    (1, 2000),  # Long chain on one qubit (beyond the recursion limit)
]

CASES = [(0, q, g) for q, g in EDGE_CASES] + [random_case(s) for s in range(50)]


def case_id(case: tuple[int, int, int]) -> str:
    seed, nb_qubits, nb_gates = case
    return f"seed{seed}-q{nb_qubits}-g{nb_gates}"


@pytest.fixture(scope="module", params=CASES, ids=case_id)
def checker(request) -> DAGChecker:
    seed, nb_qubits, nb_gates = request.param
    return DAGChecker(
        *generate_circuit_and_dag(nb_qubits, nb_gates, list(_gate_types.keys()), seed)
    )
