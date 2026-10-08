from src.qiskit2pulser.utils.Gate import Gate


class DAG:
    def __init__(self, num_qubits: int) -> None:
        self._num_qubits = num_qubits
        self._gates = []

    def add_gate(self, gate: Gate):
        self._gates.append(gate)
