from qiskit import QuantumCircuit

from src.qiskit2pulser.DAG.DAG import DAG
from src.qiskit2pulser.DAG.Gate import Gate, Gate_CZ, Gate_X, Gate_Y, Gate_Z

_gate_types = {"x": Gate_X, "y": Gate_Y, "z": Gate_Z, "cz": Gate_CZ}


def get_gate_type(name: str) -> type[Gate]:
    if name.lower() not in _gate_types:
        raise ValueError(f"get_gate_type: the gate {name} is not supported yet")
    return _gate_types[name.lower()]


def QC_to_DAG(qc: QuantumCircuit) -> DAG:
    data = qc.data
    result = DAG(qc.num_qubits)

    for e in data:
        g = get_gate_type(e.operation.name)(
            [qc.find_bit(q).index for q in e.qubits], e.operation.params
        )
        result.add_gate(g)
    return result
