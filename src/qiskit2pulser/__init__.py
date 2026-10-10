import argparse
import subprocess
import tempfile

from qiskit import QuantumCircuit


def demo_circuit() -> QuantumCircuit:
    qc = QuantumCircuit(3)
    qc.x(0)
    qc.y(1)
    qc.z(0)
    qc.x(2)
    qc.y(0)
    return qc


def show_dot(dot: str) -> None:
    """Rend le DOT en PNG avec Graphviz et l'ouvre avec le visionneur par défaut."""
    png = tempfile.NamedTemporaryFile(prefix="dag_", suffix=".png", delete=False).name
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

    from src.qiskit2pulser.qiskit_to_dag import QC_to_DAG

    qc = demo_circuit()
    print("=== Circuit Qiskit ===")
    print(qc.draw())

    dag = QC_to_DAG(qc)
    print("=== DAG ===")
    print("entrées :", [n.gate.name for n in dag.entries])

    dot = dag.to_dot_string()
    if args.dot_file:
        with open(args.dot_file, "w") as f:
            f.write(dot)
        print(f"DOT écrit dans {args.dot_file}")
    elif not args.show:
        print(dot)

    if args.show:
        show_dot(dot)
