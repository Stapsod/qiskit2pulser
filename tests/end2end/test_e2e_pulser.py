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


def total_variation(result: CompilerResult, probas: np.ndarray) -> float:
    """Distance between the sampled distribution and the exact probabilities."""
    measured = np.zeros_like(probas)
    for bitstring, count in result.counts.items():
        # Same order as Statevector.probabilities: qubit 0 is the rightmost bit
        measured[int(bitstring, 2)] = count / result.shots
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
