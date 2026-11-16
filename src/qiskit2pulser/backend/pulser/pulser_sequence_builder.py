from dataclasses import dataclass
from math import pi

from pulser import BlackmanWaveform, Pulse, Sequence

from qiskit2pulser.backend.pulser.pulser_native_gates import (
    CZ,
    PulserNativeGates,
    R,
    Rz,
)
from qiskit2pulser.DAG.DAG import DAG, Node


@dataclass
class PulserSequenceBuilder:
    def __init__(self, omega_raman, omega, device, qubits_id) -> None:
        self._omega = {
            "raman_local": omega_raman,
            "rydberg_local": omega,
        }
        # Channels are declared on first use: an unused channel changes the
        # simulation basis for nothing
        self._declared: set[str] = set()

        self.sequence = None
        self.qubits_id = qubits_id
        self.device = device

    def _translate_native_gate(self, gate: PulserNativeGates) -> None:
        if self.qubits_id == {} or self.sequence is None:
            raise RuntimeError(
                "PulserBackend.translate: The backend must be build before to translate any contracts"
            )
        match gate:
            case R((q,), theta, phi):
                self._rotation(theta, phi, q)
            case Rz((q,), phi):
                # Virtual Z: only shifts the phase of the next pulses of q.
                # Pulser needs a declared channel in the digital basis.
                self._declare("raman_local")
                self.sequence.phase_shift(phi, self.qubits_id[q], basis="digital")
            case CZ((q0, q1)):
                # pi on the control, 2pi on the target, pi on the control:
                # the Rydberg blockade gives the -1 phase
                self._add(pi, 0, "rydberg_local", q0)
                self._add(2 * pi, 0, "rydberg_local", q1)
                self._add(pi, 0, "rydberg_local", q0)
            case _:
                raise TypeError(f"PulserBackend: unsupported native gate {gate.symbol}")

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
        ch = self.device.channels[channel]
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

    def build_sequence(self, native_dag: DAG, sequence: Sequence) -> Sequence:
        self.sequence = sequence

        def translate_gate(node: Node):
            self._translate_native_gate(node.gate)

        native_dag.topological(translate_gate)

        self.sequence = None
        return sequence
