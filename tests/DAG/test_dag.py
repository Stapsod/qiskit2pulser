import pytest
import random
from qiskit import QuantumCircuit
from qiskit.circuit.library import get_standard_gate_name_mapping
from src.qiskit2pulser.qiskit_to_dag import _gate_types


def apply_gate(qc: QuantumCircuit, gate: str, *qubits: int):
    getattr(qc, gate)(*qubits)


@pytest.fixture
def generate_circuit():
    def _generate(nb_qubits: int, nb_gates: int, gates: list[str], seed: int):
        rng = random.Random(seed)
        qc = QuantumCircuit(nb_qubits)
        standard_gate_name_mapping = get_standard_gate_name_mapping()
        filtered_gates = list(
            filter(
                lambda g: standard_gate_name_mapping[g].num_qubits <= nb_qubits, gates
            )
        )
        if filtered_gates == []:
            raise IndexError("Filtered Gates set is empty.")

        for _ in range(nb_gates):
            gate = rng.choice(filtered_gates)
            num_qubits = standard_gate_name_mapping[gate].num_qubits

            apply_gate(
                qc,
                gate,
                *rng.sample(range(nb_qubits), num_qubits),
            )
        return qc

    return _generate


@pytest.mark.parametrize("seed", range(50))
def test_generator(generate_circuit, seed):
    print(generate_circuit(4, 5, list(_gate_types.keys()), seed))
