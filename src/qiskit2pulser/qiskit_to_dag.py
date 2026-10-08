from qiskit import QuantumCircuit
from src.qiskit2pulser.utils.Gate import Gate, Gate_X, Gate_Y, Gate_Z
from src.qiskit2pulser.utils.DAG import DAG

qc = QuantumCircuit(2)
qc.x(0)
qc.x(1)

_gate_types = {"x": Gate_X, "y": Gate_Y, "z": Gate_Z}


def get_gate_type(name: str) -> type[Gate]:
    if name.lower() not in _gate_types:
        raise Exception()
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


QC_to_DAG(qc)
