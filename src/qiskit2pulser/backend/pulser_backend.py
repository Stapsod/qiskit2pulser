from math import pi

from pulser import BlackmanWaveform, Pulse, Register, Sequence
from pulser_simulation import QutipEmulator

from qiskit2pulser.backend.backend import Backend
from qiskit2pulser.DAG.DAG import DAG, Node
from qiskit2pulser.layout.layout import Layout
from qiskit2pulser.parameters.layout_parameters import LayoutParameters
from qiskit2pulser.parameters.pulser_parameters import PulserParameters
from qiskit2pulser.parameters.solver_parameters import SolverParameters
from qiskit2pulser.solvers.solver_factory import make_solver
from qiskit2pulser.utils.compiler_result import CompilerResult
from qiskit2pulser.utils.contracts import CZ, Contract, R, Rz
from qiskit2pulser.utils.estimation import ResourceEstimationResult


class PulserBackend(Backend):
    parameters: PulserParameters
    register: Register
    sequence: Sequence | None = None
    cz_count: int = 0
    raman_count: int = 0

    def __init__(self, parameters: PulserParameters):
        self.parameters = parameters
        self.layout_parameters = LayoutParameters.from_pulser_parameters(
            self.parameters
        )
        self.layout = Layout(self.layout_parameters)

        # Peak amplitude per channel: raman only sets the speed, rydberg also
        # sets the blockade radius, hence the SAT threshold
        self._omega = {
            "raman_local": parameters.omega_raman,
            "rydberg_local": parameters.omega,
        }
        # Channels are declared on first use: an unused channel changes the
        # simulation basis for nothing
        self._declared: set[str] = set()

        self.sequence = None
        self.solver_parameters = None
        self.positions = None
        self.qubits_id = {}

    def _solve_positions(self):
        if self.solver_parameters is None:
            raise RuntimeError(
                "PulserBackend._solve_positions: method build must be run before"
            )

        with make_solver(self.solver_parameters) as solver:
            if solver.solve() is False:
                raise RuntimeError("aucun placement des atomes trouvé")
            solver_positions = solver.get_solution()
            self.positions = self.layout.get_positions(solver_positions)

    def _init_register(self):
        if self.positions is None:
            raise RuntimeError(
                "PulserBackend._init_register: method _solve_positions must be run before"
            )
        dic = {}
        for i in range(len(self.positions)):
            name = f"q{i}"
            dic[name] = self.positions[i]
            self.qubits_id[i] = name
        self.register = Register(dic)

    def build(self, dag: DAG) -> None:
        """Translate every gate of the DAG, each one after its predecessors."""

        if self.sequence is not None:
            raise RuntimeError("PulserBackend.build: backend must be build only once")

        self.solver_parameters = SolverParameters.from_config(
            self.parameters.config["SAT_solver"], self.layout, dag
        )

        self._solve_positions()
        self._init_register()

        def translate_gate(node: Node):
            for contract in node.gate.contracts():
                self.translate(contract)

        self.sequence = Sequence(self.register, self.parameters.device)
        dag.topological(translate_gate)
        self.sequence.measure(basis="digital")

    def translate(self, contract: Contract) -> None:
        if self.qubits_id == {} or self.sequence is None:
            raise RuntimeError(
                "PulserBackend.translate: The backend must be build before to translate any contracts"
            )
        match contract:
            case R(theta, phi, q):
                self._rotation(theta, phi, q)
            case Rz(phi, q):
                # Virtual Z: only shifts the phase of the next pulses of q.
                # Pulser needs a declared channel in the digital basis.
                self._declare("raman_local")
                self.sequence.phase_shift(phi, self.qubits_id[q], basis="digital")
            case CZ(a, b):
                # pi on the control, 2pi on the target, pi on the control:
                # the Rydberg blockade gives the -1 phase
                self._add(pi, 0, "rydberg_local", a)
                self._add(2 * pi, 0, "rydberg_local", b)
                self._add(pi, 0, "rydberg_local", a)
                self.cz_count += 1
            case _:
                raise TypeError(f"PulserBackend: unsupported contract {contract}")

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
        res = {
            "qubits_count": ResourceEstimationResult(
                "qubits_count",
                len(self.qubits_id),
                "nb qubits",
                "Number of cold atoms used in the final sequence",
            ),
            "CZ_count": ResourceEstimationResult(
                "CZ_count",
                self.cz_count,
                "nb gates",
                "Number of CZ gates in the final sequence",
            ),
            "raman_count": ResourceEstimationResult(
                "raman_count",
                self.raman_count,
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

    def _rotation(self, theta: float, phi: float, q: int) -> None:
        # A pulse area is positive: R(-theta, phi) = R(theta, phi + pi)
        if theta < 0:
            theta, phi = -theta, phi + pi
        if theta == 0:
            return
        # Pulser rotates around (cos phase, -sin phase, 0): phase = -phi
        self._add(theta, -phi, "raman_local", q)
        self.raman_count += 1

    def _declare(self, channel: str) -> None:
        if channel not in self._declared:
            self.sequence.declare_channel(channel, channel)
            self._declared.add(channel)

    def _add(self, area: float, phase: float, channel: str, q: int) -> None:
        self._declare(channel)
        self.sequence.target(self.qubits_id[q], channel)
        self.sequence.add(self._pulse(area, phase, channel), channel)

    def _duration(self, area: float, omega: float, channel: str) -> int:
        """Shortest valid duration (ns) of a Blackman pulse whose peak is <= omega."""
        ch = self.parameters.device.channels[channel]
        duration = BlackmanWaveform.from_max_val(omega, area).duration
        # Round up: a longer pulse of the same area has a lower peak
        duration = -(-duration // ch.clock_period) * ch.clock_period
        return max(duration, ch.min_duration)

    def _pulse(self, area: float, phase: float, channel: str) -> Pulse:
        omega = self._omega[channel]
        return Pulse.ConstantDetuning(
            BlackmanWaveform(self._duration(area, omega, channel), area),
            detuning=0,
            phase=phase,
        )
