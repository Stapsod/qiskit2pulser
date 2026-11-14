import argparse
import tomllib

from qiskit import QuantumCircuit

from qiskit2pulser.compiler.compiler import Compiler
from qiskit2pulser.parameters.compiler_parameters import CompilerParameters


def demo_circuit() -> QuantumCircuit:
    qc = QuantumCircuit(3)
    qc.x(0)
    qc.x(0)
    qc.x(0)
    qc.y(1)
    qc.cz(0, 1)
    qc.x(2)
    qc.y(0)
    return qc


def main() -> None:
    parser = argparse.ArgumentParser(prog="qiskit2pulser")
    parser.add_argument(
        "config_path",
        nargs="?",
        default="config.toml",
        help="chemin vers la config (config.toml par default)",
    )
    parser.add_argument("--dotfile", help="écrit le DOT dans ce fichier")
    parser.add_argument(
        "--show", action="store_true", help="affiche le graphe (Graphviz)"
    )
    args = parser.parse_args()

    with open(args.config_path, "rb") as f:
        config = tomllib.load(f)
        compiler_parameters = CompilerParameters.from_args(demo_circuit(), config, args)
        compiler = Compiler(compiler_parameters)
        compiler.build()
        result = compiler.run(1000)
    print(result)
