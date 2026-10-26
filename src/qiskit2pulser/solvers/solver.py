from abc import ABC, abstractmethod
from dataclasses import dataclass

from qiskit2pulser.parameters.solver_parameters import SolverParameters


@dataclass
class Solver(ABC):
    parameters: SolverParameters

    @abstractmethod
    def solve(self) -> bool:
        """Try to solve the SAT problem"""

    @abstractmethod
    def get_solution(self) -> list[int]:
        """Return a list with the position associated to each qubit"""

    @abstractmethod
    def _delete(self) -> None:
        """Free the resources held by the underlying solver."""

    @abstractmethod
    def _enter(self) -> None:
        """Build the solver, clauses and litterals"""

    def __enter__(self):
        # __exit__ is not called if __enter__ raises: clean up here
        try:
            self._enter()
        except BaseException:
            self._delete()
            raise
        return self

    def __exit__(self, exc_type, exc, tb):
        self._delete()
