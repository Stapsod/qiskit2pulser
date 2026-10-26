import random

from qiskit import QuantumCircuit
from qiskit.circuit.library import get_standard_gate_name_mapping

from qiskit2pulser.DAG.DAG import DAG
from qiskit2pulser.DAG.qiskit_to_dag import QC_to_DAG


def apply_gate(qc: QuantumCircuit, gate: str, *qubits: int):
    getattr(qc, gate)(*qubits)


def generate_circuit_and_dag(
    nb_qubits: int, nb_gates: int, gates: list[str], seed: int
) -> tuple[QuantumCircuit, DAG]:
    rng = random.Random(seed)
    qc = QuantumCircuit(nb_qubits)
    standard_gate_name_mapping = get_standard_gate_name_mapping()
    filtered_gates = list(
        filter(lambda g: standard_gate_name_mapping[g].num_qubits <= nb_qubits, gates)
    )
    if filtered_gates == [] and nb_gates > 0:
        raise ValueError("generate_circuit_and_dag: Filtered Gates set is empty.")

    for _ in range(nb_gates):
        gate = rng.choice(filtered_gates)
        num_qubits = standard_gate_name_mapping[gate].num_qubits

        apply_gate(
            qc,
            gate,
            *rng.sample(range(nb_qubits), num_qubits),
        )
    return (qc, QC_to_DAG(qc))
