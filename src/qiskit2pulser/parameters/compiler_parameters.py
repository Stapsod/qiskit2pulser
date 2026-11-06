from qiskit import QuantumCircuit


class CompilerParameters:
    qc: QuantumCircuit
    config_path: str
    dot_file_path: str | None
    show_dag: bool

    def __init__(self, qc: QuantumCircuit, config_path: str, args):
        self.qc = qc
        self.config_path = config_path
        self.dot_file_path = args.dot_file
        self.show_dag = args.show
