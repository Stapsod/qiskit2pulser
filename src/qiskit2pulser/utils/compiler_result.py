from dataclasses import dataclass


@dataclass
class CompilerResult:
    counts: dict[str, int]
    shots: int
    backend_name: str
    metadata: dict[str, object]
