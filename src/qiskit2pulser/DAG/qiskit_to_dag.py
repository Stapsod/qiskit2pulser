from qiskit import QuantumCircuit

from qiskit2pulser.DAG.DAG import DAG
from qiskit2pulser.DAG.logical_gate import LogicalGate, LogicalGateKind


def QC_to_DAG(qc: QuantumCircuit, apply_opti: bool = True) -> DAG:
    data = qc.data
    result = DAG(qc.num_qubits)

    for e in data:
        g = LogicalGate(
            LogicalGateKind.from_symbol(e.operation.name.lower()),
            tuple(qc.find_bit(q).index for q in e.qubits),
        )
        result.add_gate(g)

    if apply_opti:
        result.reduce_unitary_gate()
    return result
