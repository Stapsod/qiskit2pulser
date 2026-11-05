from dataclasses import dataclass, field

from pulser import BlackmanWaveform, Pulse, Register, Sequence

from qiskit2pulser.parameters.pulser_parameters import PulserParameters


class PulserBackend:
    parameters: PulserParameters
    register: Register | None = None
    sequence: Sequence | None = None

    def __init__(
        self, parameters: PulserParameters, positions: list[tuple[float, float]]
    ):
        dic = {}
        self.qubits_id = {}
        for i in range(len(positions)):
            name = f"q{i}"
            dic[name] = positions[i]
            self.qubits_id[i] = name

        self.parameters = parameters
        # Peak amplitude per channel: raman only sets the speed, rydberg also
        # sets the blockade radius, hence the SAT threshold
        self._omega = {
            "raman_local": parameters.omega_raman,
            "rydberg_local": parameters.omega,
        }
        self.register = Register(dic)
        self.sequence = Sequence(self.register, parameters.device)

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
