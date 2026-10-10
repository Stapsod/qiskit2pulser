from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from itertools import count

_gate_X_count = count()
_gate_Y_count = count()
_gate_Z_count = count()


@dataclass
class Gate(ABC):
    name: str
    qubits: set[int] = field(default_factory=set)
    params: list = field(default_factory=list)

    @abstractmethod
    def convertion(self):
        pass


@dataclass
class Gate_X(Gate):
    name: str = field(default_factory=lambda: f"X{next(_gate_X_count)}", init=False)

    def convertion(self):
        pass


@dataclass
class Gate_Y(Gate):
    name: str = field(default_factory=lambda: f"Y{next(_gate_Y_count)}", init=False)

    def convertion(self):
        pass


@dataclass
class Gate_Z(Gate):
    name: str = field(default_factory=lambda: f"Z{next(_gate_Z_count)}", init=False)

    def convertion(self):
        pass
