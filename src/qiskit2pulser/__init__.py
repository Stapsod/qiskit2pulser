import argparse
import subprocess
import tempfile

from qiskit import QuantumCircuit


def demo_circuit() -> QuantumCircuit:
    qc = QuantumCircuit(3)
    qc.x(0)
    qc.y(1)
    qc.cz(0, 1)
    qc.x(2)
    qc.y(0)
    return qc


def show_dot(dot: str) -> None:
    with tempfile.NamedTemporaryFile(prefix="dag_", suffix=".png", delete=False) as f:
        png = f.name
    subprocess.run(["dot", "-Tpng", "-o", png], input=dot, text=True, check=True)
    subprocess.Popen(["feh", png])
    print(f"Graphe ouvert : {png}")


def main() -> None:
    parser = argparse.ArgumentParser(prog="qiskit2pulser")
    parser.add_argument("dot_file", nargs="?", help="écrit le DOT dans ce fichier")
    parser.add_argument(
        "--show", action="store_true", help="affiche le graphe (Graphviz)"
    )
    args = parser.parse_args()

    from src.qiskit2pulser.DAG.qiskit_to_dag import QC_to_DAG
    from src.qiskit2pulser.layout.layout import Layout
    from src.qiskit2pulser.parameters.pulser_parameters import PulserParameters
    from src.qiskit2pulser.parameters.solver_parameters import SolverParameters
    from src.qiskit2pulser.solvers.PySAT import PySAT

    qc = demo_circuit()
    print("=== Circuit Qiskit ===")
    print(qc.draw())

    dag = QC_to_DAG(qc)
    print("=== DAG ===")
    print("entrées :", [n.name for n in dag.entries])

    dot = dag.to_dot_string()
    if args.dot_file:
        with open(f"out/{args.dot_file}", "w") as f:
            f.write(dot)
        print(f"DOT écrit dans out/{args.dot_file}")

    if args.show:
        show_dot(dot)

    pulser_parameters = PulserParameters("config.toml")
    solver_parameters = SolverParameters(pulser_parameters, qc.num_qubits)
    layout = Layout(pulser_parameters)
    with PySAT(solver_parameters, layout, dag) as solver:
        print(solver.solve())
