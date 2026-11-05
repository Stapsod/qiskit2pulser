import random

import pytest
from qiskit import QuantumCircuit

from qiskit2pulser.DAG.qiskit_to_dag import _gate_types
from qiskit2pulser.parameters.layout_parameters import LayoutParameters
from tests.circuit_generator import generate_circuit_and_dag
from tests.solvers.solver_checker import SolverChecker

# Integer steps only: the float bug of Layout must not leak into these tests
SMALL = (2, 10, 4, 6.6)  # P = 81
FOUR_NEIGHBOURS = (4, 12, 4, 4)  # Only the 4 direct neighbours are in CZ range
TINY = (2, 2, 4, 6.6)  # P = 5, at most 2 atoms fit
SINGLE = (4, 3, 4, 4)  # P = 1
DEVICE = (4, 50, 4, 6.6)  # DigitalAnalogDevice, step 4 (P = 489)

# (id, nb_qubits, cz pairs, layout parameters, expected answer)
KNOWN_CASES = [
    pytest.param(1, [], SINGLE, True, id="one-qubit-one-location"),
    pytest.param(2, [(0, 1)], SMALL, True, id="one-cz"),
    pytest.param(2, [(0, 1), (0, 1)], SMALL, True, id="same-cz-twice"),
    pytest.param(5, [(i, i + 1) for i in range(4)], SMALL, True, id="cz-chain"),
    pytest.param(5, [(0, i) for i in range(1, 5)], FOUR_NEIGHBOURS, True, id="star-4"),
    pytest.param(10, [], DEVICE, True, id="device-no-cz"),
    pytest.param(2, [], TINY, True, id="tiny-2-qubits"),
    pytest.param(3, [], TINY, False, id="tiny-3-qubits"),
    pytest.param(2, [], SINGLE, False, id="more-qubits-than-locations"),
    pytest.param(
        3, [(0, 1), (1, 2), (0, 2)], FOUR_NEIGHBOURS, False, id="triangle-bipartite"
    ),
    pytest.param(6, [(0, i) for i in range(1, 6)], FOUR_NEIGHBOURS, False, id="star-5"),
]

RANDOM_LAYOUTS = [SMALL, FOUR_NEIGHBOURS, (1, 6, 4, 5), (4, 16, 4, 6.6)]


def build_circuit(nb_qubits: int, cz: list[tuple[int, int]]) -> QuantumCircuit:
    qc = QuantumCircuit(nb_qubits)
    for a, b in cz:
        qc.cz(a, b)
    return qc


def random_case(seed: int):
    rng = random.Random(f"solver-{seed}")
    nb_qubits, nb_gates = rng.randint(1, 6), rng.randint(0, 15)
    qc, _ = generate_circuit_and_dag(
        nb_qubits, nb_gates, list(_gate_types.keys()), seed
    )
    params = rng.choice(RANDOM_LAYOUTS)
    return pytest.param(
        (qc, params), id=f"seed{seed}-q{nb_qubits}-g{nb_gates}-{params}"
    )


def known_as_checker_case(case):
    nb_qubits, cz, params, _ = case.values
    return pytest.param(
        (build_circuit(nb_qubits, cz), params), id=case.id, marks=case.marks
    )


CASES = [known_as_checker_case(c) for c in KNOWN_CASES] + [
    random_case(s) for s in range(40)
]


@pytest.fixture(scope="module", params=CASES)
def solver_checker(request) -> SolverChecker:
    qc, params = request.param
    return SolverChecker(qc, LayoutParameters(*params))
