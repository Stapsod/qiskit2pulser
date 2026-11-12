from pathlib import Path

import numpy as np
import pytest
from qiskit import QuantumCircuit
from qiskit.quantum_info import Statevector

from qiskit2pulser import Compiler
from qiskit2pulser.parameters.compiler_parameters import CompilerParameters
from qiskit2pulser.utils.compiler_result import CompilerResult

CONFIG = str(Path(__file__).parents[2] / "config.toml")
SHOTS = 100
# Margin over the expected sampling noise, so that the test is not flaky
SHOT_NOISE_MARGIN = 2
# Population error of one CZ at the 6 µm threshold of config.toml (pulses.typ)
CZ_ERROR = 0.01


def sampled_probas(result: CompilerResult, size: int) -> np.ndarray:
    """Sampled distribution, as an array of `size` probabilities."""
    measured = np.zeros(size)
    for bitstring, count in result.counts.items():
        # Same order as Statevector.probabilities: qubit 0 is the rightmost bit
        measured[int(bitstring, 2)] = count / result.shots
    return measured


def total_variation(result: CompilerResult, probas: np.ndarray) -> float:
    """Distance between the sampled distribution and the given probabilities."""
    measured = sampled_probas(result, probas.size)
    return float(np.abs(measured - probas).sum() / 2)


def tolerance(qc: QuantumCircuit, shots: int) -> float:
    """Allowed distance: sampling noise (random) plus CZ error (systematic)."""
    shot_noise = 0.5 * np.sqrt(2**qc.num_qubits / shots)
    return SHOT_NOISE_MARGIN * shot_noise + CZ_ERROR * qc.count_ops().get("cz", 0)


def get_probas(qc: QuantumCircuit):
    probs = np.round(Statevector.from_instruction(qc).probabilities(), 3)
    return probs


def get_qc_and_proba(i: int) -> tuple[QuantumCircuit, np.ndarray]:
    if i == 0:
        qc = QuantumCircuit(3)
        qc.x(0)
        qc.y(1)
        qc.cz(0, 1)
        qc.x(2)
        qc.y(0)
        return qc, get_probas(qc)
    elif i == 1:
        # Bell state: without the CZ, qubit 1 would simply return to |0>
        qc = QuantumCircuit(2)
        qc.h(0)
        qc.h(1)
        qc.cz(0, 1)
        qc.h(1)
        return qc, get_probas(qc)
    elif i == 2:
        # H Z H = X: without the Z, the qubit would return to |0>
        qc = QuantumCircuit(1)
        qc.h(0)
        qc.z(0)
        qc.h(0)
        return qc, get_probas(qc)
    elif i == 3:
        # GHZ state: two chained CZ acting on different pairs of atoms
        qc = QuantumCircuit(3)
        qc.h(0)
        qc.h(1)
        qc.cz(0, 1)
        qc.h(1)
        qc.h(2)
        qc.cz(1, 2)
        qc.h(2)
        return qc, get_probas(qc)
    else:
        raise RuntimeError("E2E_pulser.demo_circuit unknown circuit index")


@pytest.mark.parametrize("index", [0, 1, 2, 3])
def test_circuit(index: int):
    qc, probas = get_qc_and_proba(index)
    compiler_parameters = CompilerParameters(qc, CONFIG)
    compiler = Compiler(compiler_parameters)
    compiler.build()
    result = compiler.run(1000)
    assert total_variation(result, probas) <= tolerance(qc, result.shots)


# Circuits with gates that the optimisation removes:
# (nb_qubits, operations, number of gates left after the optimisation)
OPTIMISABLE_CIRCUITS = {
    "odd_run": (1, [("x", 0), ("x", 0), ("x", 0)], 1),
    "all_cancelled": (1, [("x", 0), ("x", 0)], 0),
    "nested_pairs": (
        2,
        [("h", 0), ("x", 0), ("y", 0), ("y", 0), ("x", 0), ("h", 0), ("x", 1)],
        1,
    ),
    # The pairs start a wire and sit in the middle of another one
    "bell_with_pairs": (
        2,
        [
            ("x", 0),
            ("x", 0),
            ("h", 0),
            ("h", 1),
            ("z", 1),
            ("z", 1),
            ("cz", 0, 1),
            ("h", 1),
        ],
        4,
    ),
    # X CZ X is not reducible: only the Y pair can go
    "cz_blocks_the_pair": (
        2,
        [
            ("h", 0),
            ("h", 1),
            ("x", 0),
            ("cz", 0, 1),
            ("x", 0),
            ("h", 1),
            ("y", 1),
            ("y", 1),
        ],
        6,
    ),
    # The CZ only becomes an entry of the DAG once both pairs are gone
    "cz_becomes_entry": (
        2,
        [("x", 1), ("x", 1), ("x", 0), ("x", 0), ("cz", 0, 1), ("x", 0)],
        2,
    ),
    # Two CZ in a row on qubit 0 are not a pair: they act on different atoms
    "different_cz_on_a_wire": (
        3,
        [
            ("h", 0),
            ("x", 1),
            ("y", 2),
            ("y", 2),
            ("cz", 0, 1),
            ("cz", 0, 2),
            ("h", 0),
        ],
        5,
    ),
}


def compile_and_run(
    qc: QuantumCircuit, apply_opti: bool
) -> tuple[Compiler, CompilerResult]:
    compiler = Compiler(CompilerParameters(qc, CONFIG, apply_opti=apply_opti))
    compiler.build()
    return compiler, compiler.run(1000)


def count_gates(compiler: Compiler) -> int:
    gates = []
    compiler.dag.topological(gates.append)
    return len(gates)


@pytest.mark.parametrize(
    "circuit", OPTIMISABLE_CIRCUITS.values(), ids=OPTIMISABLE_CIRCUITS.keys()
)
def test_optimisation_preserves_results(circuit):
    nb_qubits, operations, gates_left = circuit
    qc = QuantumCircuit(nb_qubits)
    for name, *qubits in operations:
        getattr(qc, name)(*qubits)

    before, result_before = compile_and_run(qc, apply_opti=False)
    after, result_after = compile_and_run(qc, apply_opti=True)

    assert count_gates(before) == qc.size()
    assert count_gates(after) == gates_left
    # Both distributions are sampled, so their noises add up quadratically
    distance = total_variation(
        result_after, sampled_probas(result_before, 2**nb_qubits)
    )
    assert distance <= np.sqrt(2) * tolerance(qc, result_after.shots)
