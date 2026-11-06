from abc import ABC, abstractmethod

from qiskit2pulser.DAG.DAG import DAG
from qiskit2pulser.parameters.backend_parameters import BackendParameters
from qiskit2pulser.utils.compiler_result import CompilerResult
from qiskit2pulser.utils.contracts import Contract


class Backend(ABC):
    parameters: BackendParameters

    @abstractmethod
    def build(self, dag: DAG):
        pass

    @abstractmethod
    def translate(self, contract: Contract):
        pass

    @abstractmethod
    def run(self, shots: int) -> CompilerResult:
        pass
