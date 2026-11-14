from qiskit import QuantumCircuit


class CompilerParameters:
    qc: QuantumCircuit
    config: dict[str, dict[str, str]]
    dot_file_path: str | None
    show_dag: bool
    apply_opti: bool

    def __init__(
        self,
        qc: QuantumCircuit,
        config: dict[str, dict[str, str]],
        dot_file_path: str | None = None,
        show_dag: bool = False,
        apply_opti: bool = True,
    ):
        self.qc = qc
        self.config = config
        self.dot_file_path = dot_file_path
        self.show_dag = show_dag
        self.apply_opti = apply_opti

    @classmethod
    def from_args(cls, qc: QuantumCircuit, config: dict[str, dict[str, str]], args):
        return cls(qc, config, args.dotfile, args.show)
