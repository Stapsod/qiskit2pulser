from pathlib import Path

from qiskit import QuantumCircuit

from qiskit2pulser.backend.backend_factory import make_backend, make_backend_parameters
from qiskit2pulser.DAG.qiskit_to_dag import QC_to_DAG

CONFIG = Path(__file__).parents[2] / "config.toml"
SHOTS = 100


def run(qc: QuantumCircuit, positions: list[tuple[float, float]]) -> dict[str, int]:
    parameters = make_backend_parameters(CONFIG)
    parameters.add_positions(positions)
    backend = make_backend(parameters)
    backend.build(QC_to_DAG(qc))
    return backend.run(SHOTS).counts


def test_circuit_with_only_a_z():
    qc = QuantumCircuit(1)
    qc.z(0)
    assert run(qc, [(0.0, 0.0)]) == {"0": SHOTS}


def test_circuit_with_only_cz():
    qc = QuantumCircuit(2)
    qc.cz(0, 1)
    assert run(qc, [(0.0, 0.0), (5.0, 0.0)]) == {"00": SHOTS}
