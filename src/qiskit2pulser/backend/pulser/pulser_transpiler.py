from dataclasses import dataclass
from math import pi
from typing import assert_never

from qiskit2pulser.backend.pulser.pulser_native_gates import CZ, R, Rz
from qiskit2pulser.DAG.DAG import DAG, Node
from qiskit2pulser.DAG.logical_gate import LogicalGate, LogicalGateKind


@dataclass
class PulserTranspiler:
    logical_dag: DAG
    _native_dag: DAG | None = None

    def _logical_to_native(self, gate: LogicalGate) -> None:
        # if self.qubits_id == {} or self.sequence is None:
        #     raise RuntimeError(
        #         "PulserBackend.translate: The backend must be build before to translate any contracts"
        #     )
        if self._native_dag is None:
            raise RuntimeError(
                "PulserTranspiler.get__native_dag: native DAG must be built before"
            )

        match gate.kind:
            case LogicalGateKind.X:
                self._native_dag.add_gate(R(gate.qubits, pi, 0))
            case LogicalGateKind.Y:
                self._native_dag.add_gate(R(gate.qubits, pi, pi / 2))
            case LogicalGateKind.Z:
                self._native_dag.add_gate(Rz(gate.qubits, pi))
            case LogicalGateKind.H:
                self._native_dag.add_gate(Rz(gate.qubits, pi))
                self._native_dag.add_gate(R(gate.qubits, pi / 2, pi / 2))
            case LogicalGateKind.CZ:
                self._native_dag.add_gate(CZ(gate.qubits))
            case _:
                assert_never(gate.kind)

    def build_native_dag(self) -> DAG:
        self._native_dag = DAG(self.logical_dag.num_qubits)

        def translate_gate(node: Node):
            self._logical_to_native(node.gate)

        self.logical_dag.topological(translate_gate)
        return self._native_dag

    def get_native_dag(self) -> DAG:
        if self._native_dag is None:
            raise RuntimeError(
                "PulserTranspiler.get__native_dag: native DAG must be built before"
            )
        return self._native_dag
