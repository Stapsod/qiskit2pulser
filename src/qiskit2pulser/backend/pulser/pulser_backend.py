from pulser import Register, Sequence
from pulser_simulation import QutipEmulator

from qiskit2pulser.backend.pulser.pulser_native_gates import CZ, R
from qiskit2pulser.backend.pulser.pulser_register_builder import PulserRegisterBuilder
from qiskit2pulser.backend.pulser.pulser_sequence_builder import PulserSequenceBuilder
from qiskit2pulser.backend.pulser.pulser_transpiler import PulserTranspiler
from qiskit2pulser.backend.utils.backend import Backend
from qiskit2pulser.DAG.DAG import DAG, Node
from qiskit2pulser.parameters.layout_parameters import LayoutParameters
from qiskit2pulser.parameters.pulser_parameters import PulserParameters
from qiskit2pulser.utils.compiler_result import CompilerResult
from qiskit2pulser.utils.estimation import ResourceEstimationResult


class PulserBackend(Backend):
    parameters: PulserParameters
    register: Register
    sequence: Sequence | None = None

    def __init__(self, parameters: PulserParameters):
        self.parameters = parameters

    def build(self, dag: DAG) -> None:
        """Translate every gate of the DAG, each one after its predecessors."""

        if self.sequence is not None:
            raise RuntimeError("PulserBackend.build: backend must be build only once")

        self.transpiler = PulserTranspiler(dag)
        self.transpiler.build_native_dag()
        self.native_dag = self.transpiler.get_native_dag()

        self.register_builder = PulserRegisterBuilder(
            self.parameters.config["SAT_solver"],
            LayoutParameters.from_pulser_parameters(self.parameters),
            self.native_dag,
        )
        self.register = self.register_builder.build_register()
        self.qubits_id = self.register_builder.get_qubits_id()

        self.sequence_builder = PulserSequenceBuilder(
            self.parameters.omega_raman,
            self.parameters.omega,
            self.parameters.device,
            self.qubits_id,
        )

        self.sequence = Sequence(self.register, self.parameters.device)
        self.sequence_builder.build_sequence(self.native_dag, self.sequence)
        self.sequence.measure(basis="digital")

    def run(self, shots: int = 1000) -> CompilerResult:
        if self.sequence is None:
            raise RuntimeError(
                "PulserBackend.run: The backend must be build before to be run"
            )
        if (
            "raman_local" not in self.sequence.declared_channels
            or self.sequence.get_duration("raman_local") == 0
        ):
            return CompilerResult(
                {"".join(["0" for _ in range(len(self.qubits_id))]): shots},
                shots,
                "pulser",
                {},
            )
        res = QutipEmulator.from_sequence(self.sequence).run()
        dic = {
            k[::-1]: v for k, v in dict(res.sample_final_state(N_samples=shots)).items()
        }
        return CompilerResult(dic, shots, "pulser", {})

    def resource_estimation(self) -> dict[str, ResourceEstimationResult]:
        if self.sequence is None:
            raise RuntimeError(
                "PulserBackend.resource_estimation: The backend must be build before to get the resource estimation"
            )

        # One native gate gives one instruction: count them on the native DAG.
        # An R with theta = 0 emits no pulse (see PulserSequenceBuilder).
        cz_count = 0
        raman_count = 0

        def count(node: Node) -> None:
            nonlocal cz_count, raman_count
            match node.gate:
                case CZ():
                    cz_count += 1
                case R(theta=theta) if theta != 0:
                    raman_count += 1

        self.native_dag.bfs(count)

        res = {
            "qubits_count": ResourceEstimationResult(
                "qubits_count",
                len(self.qubits_id),
                "nb qubits",
                "Number of cold atoms used in the final sequence",
            ),
            "CZ_count": ResourceEstimationResult(
                "CZ_count",
                cz_count,
                "nb gates",
                "Number of CZ gates in the final sequence",
            ),
            "raman_count": ResourceEstimationResult(
                "raman_count",
                raman_count,
                "nb raman pulse",
                "Number of Raman pulses in the final sequence",
            ),
            "duration": ResourceEstimationResult(
                "duration",
                int(self.sequence.get_duration()),
                "ns",
                "Duration of the final sequence in ns",
            ),
        }
        return res
