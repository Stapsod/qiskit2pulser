"""Native operations: the contract between the gates and the backends.

Each gate decomposes into an ordered list of contracts, and each backend
translates every contract into its own instructions. Rotations follow
Qiskit's convention: R(theta, phi) rotates by theta around the axis
(cos phi, sin phi, 0) of the Bloch sphere.
"""

from dataclasses import dataclass
from typing import ClassVar

from qiskit2pulser.backend.utils.native_gates import NativeGates


@dataclass(frozen=True)
class R(NativeGates):
    """Rotation by theta around an axis of the equatorial plane."""

    theta: float
    phi: float
    symbol: ClassVar[str] = "R"
    arity: ClassVar[int] = 1


@dataclass(frozen=True)
class Rz(NativeGates):
    """Rotation by phi around the Z axis."""

    phi: float
    symbol: ClassVar[str] = "Rz"
    arity: ClassVar[int] = 1


@dataclass(frozen=True)
class CZ(NativeGates):
    """Symmetric: the backend chooses which qubit is the control."""

    symbol: ClassVar[str] = "CZ"
    arity: ClassVar[int] = 2

    def __post_init__(self) -> None:
        super().__post_init__()
        object.__setattr__(self, "qubits", tuple(sorted(self.qubits)))


PulserNativeGates = R | Rz | CZ
