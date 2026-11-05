"""Native operations: the contract between the gates and the backends.

Each gate decomposes into an ordered list of contracts, and each backend
translates every contract into its own instructions. Rotations follow
Qiskit's convention: R(theta, phi) rotates by theta around the axis
(cos phi, sin phi, 0) of the Bloch sphere.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class R:
    """Rotation by theta around an axis of the equatorial plane."""

    theta: float
    phi: float
    qubit: int


@dataclass(frozen=True)
class Rz:
    """Rotation by phi around the Z axis."""

    phi: float
    qubit: int


@dataclass(frozen=True)
class CZ:
    """Symmetric: the backend chooses which qubit is the control."""

    a: int
    b: int


Contract = R | Rz | CZ
