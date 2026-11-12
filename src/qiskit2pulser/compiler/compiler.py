import subprocess
import tempfile

from qiskit2pulser.backend.backend_factory import make_backend, make_backend_parameters
from qiskit2pulser.DAG.qiskit_to_dag import QC_to_DAG
from qiskit2pulser.layout.layout import Layout
from qiskit2pulser.parameters.compiler_parameters import CompilerParameters
from qiskit2pulser.parameters.layout_parameters import LayoutParameters
from qiskit2pulser.parameters.solver_parameters import SolverParameters
from qiskit2pulser.solvers.solver_factory import make_solver
from qiskit2pulser.utils.compiler_result import CompilerResult


class Compiler:
    def __init__(self, parameters: CompilerParameters):
        self.parameters = parameters
        self.backend_parameters = make_backend_parameters(self.parameters.config_path)
        self.layout_parameters = LayoutParameters.from_pulser_parameters(
            self.backend_parameters
        )
        self.layout = Layout(self.layout_parameters)

        self.dag = None
        self.solver_parameters = None

        self.solver_positions = None

        self.backend = None

    def _show_dot(self, dot: str) -> None:
        with tempfile.NamedTemporaryFile(
            prefix="dag_", suffix=".png", delete=False
        ) as f:
            png = f.name
        subprocess.run(["dot", "-Tpng", "-o", png], input=dot, text=True, check=True)
        subprocess.Popen(["feh", png])
        print(f"Graphe ouvert : {png}")

    def _convert_to_DAG(self):
        self.dag = QC_to_DAG(self.parameters.qc, self.parameters.apply_opti)
        self.solver_parameters = SolverParameters.from_config(
            self.parameters.config_path, self.layout, self.dag
        )

        dot = self.dag.to_dot_string()
        if self.parameters.dot_file_path:
            with open(f"out/{self.parameters.dot_file_path}", "w") as f:
                f.write(dot)
            print(f"DOT écrit dans out/{self.parameters.dot_file_path}")

        if self.parameters.show_dag:
            self._show_dot(dot)

    def _solve_positions(self):
        if self.solver_parameters is None:
            raise RuntimeError(
                "Compiler.solve_positions: method _convert_to_DAG must be run before"
            )

        with make_solver(self.solver_parameters) as solver:
            if solver.solve() is False:
                raise RuntimeError("aucun placement des atomes trouvé")
            self.solver_positions = solver.get_solution()

    def _convert_to_backend(self):
        if self.solver_positions is None or self.dag is None:
            raise RuntimeError(
                "Compiler.convert_to_backend: methods _convert_to_DAG and solver_positions must be run before"
            )
        positions = self.layout.get_positions(self.solver_positions)
        self.backend_parameters.add_positions(positions)
        self.backend = make_backend(self.backend_parameters)
        self.backend.build(self.dag)

    def build(self):
        self._convert_to_DAG()
        self._solve_positions()
        self._convert_to_backend()

    def run(self, shot: int) -> CompilerResult:
        if self.backend is None:
            raise RuntimeError("Compiler.run: backend is None")
        return self.backend.run(shot)
