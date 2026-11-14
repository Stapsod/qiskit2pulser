from dataclasses import dataclass
from typing import Any


@dataclass
class ResourceEstimationResult:
    name: str
    value: Any
    unit: str
    description: str
