from dataclasses import dataclass

from qiskit2pulser.DAG.DAG import DAG
from qiskit2pulser.layout.layout import Layout


@dataclass
class SolverParameters:
    type: str
    name: str
    layout: Layout
    dag: DAG

    @classmethod
    def from_config(
        cls, config: dict[str, str], layout: Layout, dag: DAG
    ) -> "SolverParameters":
        return cls(config["type"], config["name"], layout, dag)
