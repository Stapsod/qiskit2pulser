from abc import ABC, abstractmethod

from qiskit2pulser.DAG.DAG import DAG
from qiskit2pulser.parameters.backend_parameters import BackendParameters
from qiskit2pulser.utils.compiler_result import CompilerResult
from qiskit2pulser.utils.contracts import Contract
from qiskit2pulser.utils.estimation import ResourceEstimationResult


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

    @abstractmethod
    def resource_estimation(self) -> dict[str, ResourceEstimationResult]:
        pass
