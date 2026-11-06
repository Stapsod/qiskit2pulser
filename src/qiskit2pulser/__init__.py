import argparse

from qiskit import QuantumCircuit

from qiskit2pulser.compiler.compiler import Compiler
from qiskit2pulser.parameters.compiler_parameters import CompilerParameters


def demo_circuit() -> QuantumCircuit:
    qc = QuantumCircuit(3)
    qc.x(0)
    qc.y(1)
    qc.cz(0, 1)
    qc.x(2)
    qc.y(0)
    return qc


def main() -> None:
    parser = argparse.ArgumentParser(prog="qiskit2pulser")
    parser.add_argument("dot_file", nargs="?", help="écrit le DOT dans ce fichier")
    parser.add_argument(
        "--show", action="store_true", help="affiche le graphe (Graphviz)"
    )
    args = parser.parse_args()
    compiler_parameters = CompilerParameters(demo_circuit(), "config.toml", args)
    compiler = Compiler(compiler_parameters)
    compiler.build()
