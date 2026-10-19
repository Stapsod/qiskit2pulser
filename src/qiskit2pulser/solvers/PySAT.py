from dataclasses import dataclass, field

from src.qiskit2pulser.solvers.solver import Solver


@dataclass
class PySAT(Solver):
    _variables_x: list[list[int]] = field(init=False)
    _variables_s: list[list[int]] = field(init=False)
    _variables_t: list[list[int]] = field(init=False)

    def __post_init__(self):
        self._variables_x = []

    def encode(self, cz: set[tuple[int, int]]):
        pass
