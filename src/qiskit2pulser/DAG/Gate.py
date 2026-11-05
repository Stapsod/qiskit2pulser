from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import ClassVar


@dataclass
class Gate(ABC):
    symbol: ClassVar[str]
    qubits: list[int] = field(default_factory=list)
    params: list = field(default_factory=list)

    @abstractmethod
    def convertion(self):
        pass


class Gate_X(Gate):
    symbol = "x"

    def convertion(self):
        pass


class Gate_Y(Gate):
    symbol = "y"

    def convertion(self):
        pass


class Gate_Z(Gate):
    symbol = "z"

    def convertion(self):
        pass


class Gate_CZ(Gate):
    symbol = "cz"

    def convertion(self):
        pass
