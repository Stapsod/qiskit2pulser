from dataclasses import dataclass, field

from qiskit import QuantumCircuit

from qiskit2pulser.DAG.qiskit_to_dag import QC_to_DAG
from qiskit2pulser.layout.layout import Layout
from qiskit2pulser.parameters.layout_parameters import LayoutParameters
from qiskit2pulser.parameters.solver_parameters import SolverParameters
from qiskit2pulser.solvers.solver_factory import make_solver


@dataclass
class SolverChecker:
    qc: QuantumCircuit
    layout_params: LayoutParameters
    solver_type: str = "pysat"
    solver_name: str = "cadical195"
    layout: Layout = field(init=False)
    cz_pairs: set[tuple[int, int]] = field(init=False)
    is_sat: bool = field(init=False)
    solution: list[int] | None = field(init=False)

    def __post_init__(self):
        self.layout = Layout(self.layout_params)
        # Read straight from the circuit, independently of the DAG and its bfs
        self.cz_pairs = {
            tuple(sorted(self.qc.find_bit(q).index for q in instr.qubits))
            for instr in self.qc.data
            if instr.operation.name == "cz"
        }
        params = SolverParameters(
            self.solver_type, self.solver_name, self.layout, QC_to_DAG(self.qc)
        )
        with make_solver(params) as solver:
            self.is_sat = solver.solve()
            self.solution = solver.get_solution() if self.is_sat else None

    def check_solution_shape(self):
        if not self.is_sat:
            return
        assert len(self.solution) == self.qc.num_qubits, (
            f"SolverChecker.check_solution_shape: expected one location per qubit ({self.qc.num_qubits}), got {len(self.solution)}"
        )
        for q, p in enumerate(self.solution):
            assert 0 <= p < self.layout.nb_points, (
                f"SolverChecker.check_solution_shape: qubit {q} is on location {p}, outside [0, {self.layout.nb_points})"
            )

    def check_distinct_locations(self):
        if not self.is_sat:
            return
        assert len(set(self.solution)) == len(self.solution), (
            f"SolverChecker.check_distinct_locations: several qubits share a location: {self.solution}"
        )

    def check_min_distance(self):
        if not self.is_sat:
            return
        n = len(self.solution)
        for a in range(n):
            for b in range(a + 1, n):
                pa, pb = self.solution[a], self.solution[b]
                assert not self.layout.too_close(pa, pb), (
                    f"SolverChecker.check_min_distance: qubits {a} and {b} are {self.layout.distance(pa, pb)} µm apart (min {self.layout.min_dist})"
                )

    def check_cz_range(self):
        if not self.is_sat:
            return
        for a, b in self.cz_pairs:
            pa, pb = self.solution[a], self.solution[b]
            assert self.layout.in_cz_range(pa, pb), (
                f"SolverChecker.check_cz_range: cz({a}, {b}) at {self.layout.distance(pa, pb)} µm, expected in [{self.layout.min_dist}, {self.layout.threshold}]"
            )
