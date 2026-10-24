import tomllib
from pathlib import Path

from pulser.devices import Device, DigitalAnalogDevice


class PulserParameters:
    def __init__(
        self,
        config_path: str | Path,
        device: Device = DigitalAnalogDevice,
    ) -> None:
        with open(config_path, "rb") as f:
            config = tomllib.load(f)["pulser"]
        # Device constants (µm, rad/µs, rad.µm^6/µs)
        self.device = device
        self.min_dist = float(device.min_atom_distance)
        self.max_radius = float(device.max_radial_distance)
        self.max_atoms = device.max_atom_num
        self.interaction_coeff = device.interaction_coeff
        self.max_omega = device.channels["rydberg_local"].max_amp

        # Configuration choices
        self.omega = float(config["omega"])
        self.step = float(config["step"])
        if not 0 < self.omega <= self.max_omega:
            raise ValueError(f"omega must be in ]0, {self.max_omega}] rad/µs")

        # Derived values
        self.blockade_radius = device.rydberg_blockade_radius(self.omega)
        # Optional in the config: defaults to the blockade radius
        self.threshold = float(config.get("threshold", self.blockade_radius))

        self._check()

    def _check(self) -> None:
        if self.step <= 0:
            raise ValueError("step must be positive")
        if not self.min_dist <= self.threshold <= self.blockade_radius:
            raise ValueError(
                f"threshold must be in [{self.min_dist}, "
                f"{self.blockade_radius:.2f}] µm for omega = {self.omega}"
            )
