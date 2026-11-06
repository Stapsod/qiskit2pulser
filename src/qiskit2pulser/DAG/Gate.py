from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from math import pi
from typing import ClassVar

from qiskit2pulser.utils.contracts import CZ, Contract, R, Rz


@dataclass
class Gate(ABC):
    symbol: ClassVar[str]
    qubits: list[int] = field(default_factory=list)
    params: list = field(default_factory=list)

    @abstractmethod
    def contracts(self) -> list[Contract]:
        """Native operations equivalent to the gate (up to a global phase), in order."""


class Gate_X(Gate):
    symbol = "x"

    def contracts(self) -> list[Contract]:
        return [R(pi, 0, self.qubits[0])]


class Gate_Y(Gate):
    symbol = "y"

    def contracts(self) -> list[Contract]:
        return [R(pi, pi / 2, self.qubits[0])]


class Gate_Z(Gate):
    symbol = "z"

    def contracts(self) -> list[Contract]:
        return [Rz(pi, self.qubits[0])]


class Gate_H(Gate):
    symbol = "h"

    def contracts(self) -> list[Contract]:
        # H = R_y(pi/2) . Z, the Z being applied first
        q = self.qubits[0]
        return [Rz(pi, q), R(pi / 2, pi / 2, q)]


class Gate_CZ(Gate):
    symbol = "cz"

    def contracts(self) -> list[Contract]:
        return [CZ(self.qubits[0], self.qubits[1])]
