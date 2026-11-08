from qiskit import QuantumCircuit


class CompilerParameters:
    qc: QuantumCircuit
    config_path: str
    dot_file_path: str | None
    show_dag: bool

    def __init__(
        self,
        qc: QuantumCircuit,
        config_path: str,
        dot_file_path: str | None = None,
        show_dag: bool = False,
    ):
        self.qc = qc
        self.config_path = config_path
        self.dot_file_path = dot_file_path
        self.show_dag = show_dag

    @classmethod
    def from_args(cls, qc: QuantumCircuit, config_path: str, args):
        return cls(qc, config_path, args.dot_file, args.show)
