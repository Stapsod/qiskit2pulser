from dataclasses import dataclass

from src.qiskit2pulser.parameters.pulser_parameters import PulserParameters


@dataclass
class SolverParameters:
    pulser_parameters: PulserParameters
    nb_qubits: int
