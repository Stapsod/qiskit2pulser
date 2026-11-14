from typing import Any

from qiskit import QuantumCircuit


class CompilerParameters:
    qc: QuantumCircuit
    config: dict[str, dict[str, Any]]
    dot_file_path: str | None
    show_dag: bool

    def __init__(
        self,
        qc: QuantumCircuit,
        config: dict[str, dict[str, Any]],
        dot_file_path: str | None = None,
        show_dag: bool = False,
    ):
        self.qc = qc
        self.config = config
        self.dot_file_path = dot_file_path
        self.show_dag = show_dag

    @classmethod
    def from_args(cls, qc: QuantumCircuit, config: dict[str, dict[str, Any]], args):
        return cls(qc, config, args.dotfile, args.show)
