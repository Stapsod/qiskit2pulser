from abc import ABC, abstractmethod
from enum import Enum


class Gate(ABC):
    def __init__(self, name: str, qubits: list, params: list) -> None:
        self._name = name
        self._params = params
        self._qubits = qubits

    def __str__(self) -> str:
        return f"{self._name}, {self._params}, {self._qubits}\n"

    @abstractmethod
    def convertion(self):
        pass


class Gate_X(Gate):
    def __init__(self, qubits: list, params: list):
        super().__init__("X", qubits, params)

    def convertion(self):
        pass


class Gate_Y(Gate):
    def __init__(self, qubits: list, params: list):
        super().__init__("Y", qubits, params)

    def convertion(self):
        pass


class Gate_Z(Gate):
    def __init__(self, qubits: list, params: list):
        super().__init__("Z", qubits, params)

    def convertion(self):
        pass
