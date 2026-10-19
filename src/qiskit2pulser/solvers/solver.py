from abc import ABC, abstractmethod
from dataclasses import dataclass

from src.qiskit2pulser.parameters.solver_parameters import SolverParameters


@dataclass
class Solver(ABC):
    parameters: SolverParameters

    @abstractmethod
    def encode(self, cz: set[tuple[int, int]]):
        pass
