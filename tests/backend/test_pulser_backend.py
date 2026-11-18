from qiskit import QuantumCircuit

from qiskit2pulser.backend.utils.backend_factory import (
    make_backend,
    make_backend_parameters,
)
from qiskit2pulser.DAG.qiskit_to_dag import QC_to_DAG
from tests.config import make_config

SHOTS = 100


def run(qc: QuantumCircuit) -> dict[str, int]:
    parameters = make_backend_parameters(make_config())
    backend = make_backend(parameters)
    backend.build(QC_to_DAG(qc))
    return backend.run(SHOTS).counts


def test_circuit_with_only_a_z():
    qc = QuantumCircuit(1)
    qc.z(0)
    assert run(qc) == {"0": SHOTS}


def test_circuit_with_only_cz():
    qc = QuantumCircuit(2)
    qc.cz(0, 1)
    assert run(qc) == {"00": SHOTS}
