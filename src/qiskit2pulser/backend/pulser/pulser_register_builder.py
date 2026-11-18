from dataclasses import dataclass

from pulser import Register

from qiskit2pulser.DAG.DAG import DAG
from qiskit2pulser.layout.layout import Layout
from qiskit2pulser.parameters.layout_parameters import LayoutParameters
from qiskit2pulser.parameters.solver_parameters import SolverParameters
from qiskit2pulser.solvers.solver_factory import make_solver


@dataclass()
class PulserRegisterBuilder:
    sat_config: dict[str, str]
    layout_parameters: LayoutParameters
    dag: DAG

    def __post_init__(self) -> None:
        # One Layout shared by the solver (neighbourhoods) and get_positions
        self._layout = Layout(self.layout_parameters)
        self.parameters = SolverParameters.from_config(
            self.sat_config, self._layout, self.dag
        )
        self._qubits_id = {}

    def _solve_positions(self):
        if self.parameters is None:
            raise RuntimeError(
                "PulserBackend._solve_positions: method build must be run before"
            )

        with make_solver(self.parameters) as solver:
            if solver.solve() is False:
                raise RuntimeError("aucun placement des atomes trouvé")
            solver_positions = solver.get_solution()
            self._positions = self._layout.get_positions(solver_positions)

    def _init_register(self):
        if self._positions is None:
            raise RuntimeError(
                "PulserBackend._init_register: method _solve_positions must be run before"
            )
        dic = {}
        for i in range(len(self._positions)):
            name = f"q{i}"
            dic[name] = self._positions[i]
            self._qubits_id[i] = name
        self._register = Register(dic)

    def build_register(self) -> Register:
        self._solve_positions()
        self._init_register()
        return self._register

    def get_qubits_id(self) -> dict[int, str]:
        return self._qubits_id
