import tomllib
from dataclasses import dataclass
from pathlib import Path

from qiskit2pulser.DAG.DAG import DAG
from qiskit2pulser.layout.layout import Layout
from qiskit2pulser.parameters.pulser_parameters import PulserParameters


@dataclass
class SolverParameters:
    def __init__(
        self,
        config_path: str | Path,
        pulser_parameters: PulserParameters,
        layout: Layout,
        dag: DAG,
    ) -> None:
        with open(config_path, "rb") as f:
            config = tomllib.load(f)["SAT_solver"]

        self.pulser_parameters = pulser_parameters
        self.type = config["type"]
        self.name = config["name"]
        self.layout = layout
        self.dag = dag
