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
    symbol = "X"

    def convertion(self):
        pass


class Gate_Y(Gate):
    symbol = "Y"

    def convertion(self):
        pass


class Gate_Z(Gate):
    symbol = "Z"

    def convertion(self):
        pass


class Gate_CZ(Gate):
    symbol = "CZ"

    def convertion(self):
        pass
