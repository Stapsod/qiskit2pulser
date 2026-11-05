from dataclasses import dataclass

from qiskit2pulser.parameters.pulser_parameters import PulserParameters


@dataclass
class LayoutParameters:
    step: float
    max_radius: float
    min_dist: float
    threshold: float

    def __post_init__(self):
        if self.step <= 0 or self.max_radius <= 0 or self.min_dist <= 0:
            raise ValueError("step, max_radius and min_dist must be positive")
        if not self.min_dist <= self.threshold:
            raise ValueError(f"threshold must be in more than {self.min_dist}")

    @classmethod
    def from_pulser_parameters(cls, params: PulserParameters) -> "LayoutParameters":
        return cls(params.step, params.max_radius, params.min_dist, params.threshold)
