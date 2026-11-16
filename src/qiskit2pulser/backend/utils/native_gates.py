from dataclasses import dataclass
from typing import ClassVar


@dataclass(frozen=True)
class NativeGates:
    qubits: tuple[int, ...]
    symbol: ClassVar[str]
    arity: ClassVar[int]

    def __post_init__(self) -> None:
        if len(self.qubits) != self.arity:
            raise ValueError(
                f"{self.symbol} acts on {self.arity} qubit(s), "
                f"got {len(self.qubits)}: {self.qubits}"
            )

        if len(set(self.qubits)) != len(self.qubits):
            raise ValueError(f"{self.symbol} got duplicated qubits: {self.qubits}")
