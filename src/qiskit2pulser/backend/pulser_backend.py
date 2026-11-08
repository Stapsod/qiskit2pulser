from math import pi

from pulser import BlackmanWaveform, Pulse, Register, Sequence
from pulser_simulation import QutipEmulator

from qiskit2pulser.backend.backend import Backend
from qiskit2pulser.DAG.DAG import DAG, Node
from qiskit2pulser.parameters.pulser_parameters import PulserParameters
from qiskit2pulser.utils.compiler_result import CompilerResult
from qiskit2pulser.utils.contracts import CZ, Contract, R, Rz


class PulserBackend(Backend):
    parameters: PulserParameters
    register: Register
    sequence: Sequence | None = None

    def __init__(self, parameters: PulserParameters):
        self.parameters = parameters
        dic = {}
        self.qubits_id = {}
        if self.parameters.positions is None:
            raise RuntimeError(
                "PulserBackend: cannot init a PulserBackend without positions"
            )
        for i in range(len(self.parameters.positions)):
            name = f"q{i}"
            dic[name] = self.parameters.positions[i]
            self.qubits_id[i] = name

        # Peak amplitude per channel: raman only sets the speed, rydberg also
        # sets the blockade radius, hence the SAT threshold
        self._omega = {
            "raman_local": parameters.omega_raman,
            "rydberg_local": parameters.omega,
        }
        self.register = Register(dic)
        # Channels are declared on first use: an unused channel changes the
        # simulation basis for nothing
        self._declared: set[str] = set()

    def build(self, dag: DAG) -> None:
        """Translate every gate of the DAG, each one after its predecessors."""

        if self.sequence is not None:
            raise RuntimeError("PulserBackend.build: backend must be build only once")

        def translate_gate(node: Node):
            for contract in node.gate.contracts():
                self.translate(contract)

        self.sequence = Sequence(self.register, self.parameters.device)
        dag.topological(translate_gate)
        self.sequence.measure(basis="digital")

    def translate(self, contract: Contract) -> None:
        if self.sequence is None:
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
            case _:
                raise TypeError(f"PulserBackend: unsupported contract {contract}")

    def run(self, shots: int = 1000) -> CompilerResult:
        if self.sequence is None:
            raise RuntimeError(
                "PulserBackend.run: The backend must be build before to be run"
            )
        res = QutipEmulator.from_sequence(self.sequence).run()
        dic = {
            k[::-1]: v for k, v in dict(res.sample_final_state(N_samples=shots)).items()
        }
        return CompilerResult(dic, shots, "pulser", {})

    def _rotation(self, theta: float, phi: float, q: int) -> None:
        # A pulse area is positive: R(-theta, phi) = R(theta, phi + pi)
        if theta < 0:
            theta, phi = -theta, phi + pi
        if theta == 0:
            return
        # Pulser rotates around (cos phase, -sin phase, 0): phase = -phi
        self._add(theta, -phi, "raman_local", q)

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
