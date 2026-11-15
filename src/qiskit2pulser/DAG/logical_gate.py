from dataclasses import dataclass
from enum import Enum


class LogicalGateKind(Enum):
    """Kind of a logical gate, with its backend-independent properties."""

    X = ("x", 1, "X", False)
    Y = ("y", 1, "Y", False)
    Z = ("z", 1, "Z", True)
    H = ("h", 1, "H", False)
    CZ = ("cz", 2, "CZ", True)

    def __init__(
        self, symbol: str, arity: int, inverse_name: str, is_diagonal: bool
    ) -> None:
        self.symbol = symbol
        self.arity = arity
        self._inverse_name = inverse_name
        self.is_diagonal = is_diagonal

    @property
    def inverse(self) -> "LogicalGateKind":
        """Kind of the inverse gate (resolved by name, members cannot reference each other)."""
        return LogicalGateKind[self._inverse_name]

    @classmethod
    def from_symbol(cls, symbol: str) -> "LogicalGateKind":
        """Kind matching a Qiskit gate name, e.g. "cz"."""
        for kind in cls:
            if kind.symbol == symbol:
                return kind
        raise ValueError(f"Unsupported logical gate: {symbol!r}")


@dataclass(frozen=True)
class LogicalGate:
    """A logical gate applied to some qubits."""

    kind: LogicalGateKind
    qubits: tuple[int, ...]

    def __post_init__(self) -> None:
        if len(self.qubits) != self.kind.arity:
            raise ValueError(
                f"{self.kind.name} acts on {self.kind.arity} qubit(s), "
                f"got {len(self.qubits)}: {self.qubits}"
            )
        if len(set(self.qubits)) != len(self.qubits):
            raise ValueError(f"{self.kind.name} got duplicated qubits: {self.qubits}")

    @property
    def symbol(self) -> str:
        return self.kind.symbol
