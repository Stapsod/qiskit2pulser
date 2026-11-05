import tomllib
from dataclasses import dataclass
from pathlib import Path

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
        cls, config_path: str | Path, layout: Layout, dag: DAG
    ) -> "SolverParameters":
        with open(config_path, "rb") as f:
            config = tomllib.load(f)["SAT_solver"]
        return cls(config["type"], config["name"], layout, dag)
