from dataclasses import dataclass, field

import pysat.solvers as pysat_solvers

from qiskit2pulser.DAG.DAG import Node
from qiskit2pulser.solvers.solver import Solver


@dataclass
class PySAT(Solver):
    _variable_to_litteral: dict[str, int] = field(init=False)
    solver: pysat_solvers.Solver | None = field(init=False, default=None)

    def _init_litterals(self):
        self.Q = self.parameters.dag.num_qubits
        self.P = self.parameters.layout.nb_points
        # Size of each family, the numbering starts at 1 (0 is not a literal)
        x = self.Q * self.P
        s = self.Q * (self.P - 1)
        self._variable_to_litteral = {
            "x": 1,
            "s": 1 + x,
            "t": 1 + x + s,
        }

    def _init_solver(self):
        self.solver = pysat_solvers.Solver(name=self.parameters.name)

    def _get_cz(self):
        self.cz_tuples = set()

        def use_node(node: Node):
            if node.gate.symbol == "cz":
                q1, q2 = node.gate.qubits[0], node.gate.qubits[1]
                t = (q1, q2) if q1 < q2 else (q2, q1)
                self.cz_tuples.add(t)

        self.parameters.dag.bfs(use_node)

    def _access_litterals(self, t: str, y: int, x: int) -> int:
        # x[q][p] and s[q][k] are rows of a qubit, t[p][j] is the column of a spot
        temp = self.P
        if t == "s":
            temp -= 1
        elif t == "t":
            temp = self.Q
        return self._variable_to_litteral[t] + y * temp + x

    def _at_least_one_spot(self):
        for q in range(self.Q):
            self.solver.add_clause(
                [self._access_litterals("x", q, y) for y in range(self.P)]
            )

    def _only_one_spot_per_qubit(self):
        for q in range(self.Q):
            for k in range(self.P - 1):
                self.solver.add_clause(
                    [
                        -self._access_litterals("x", q, k),
                        self._access_litterals("s", q, k),
                    ]
                )
            for k in range(1, self.P - 1):
                self.solver.add_clause(
                    [
                        -self._access_litterals("s", q, k - 1),
                        self._access_litterals("s", q, k),
                    ]
                )
            for k in range(1, self.P):
                self.solver.add_clause(
                    [
                        -self._access_litterals("s", q, k - 1),
                        -self._access_litterals("x", q, k),
                    ]
                )

    def _at_most_one_qubit_per_sport(self):
        # Extended up to t[p][Q - 1], which means "p is occupied"
        for p in range(self.P):
            for j in range(self.Q):
                self.solver.add_clause(
                    [
                        -self._access_litterals("x", j, p),
                        self._access_litterals("t", p, j),
                    ]
                )
            for j in range(1, self.Q):
                self.solver.add_clause(
                    [
                        -self._access_litterals("t", p, j - 1),
                        self._access_litterals("t", p, j),
                    ]
                )
                self.solver.add_clause(
                    [
                        -self._access_litterals("t", p, j - 1),
                        -self._access_litterals("x", j, p),
                    ]
                )

    def _minimal_distance(self):
        for p1, p2 in self.parameters.layout.too_close_pairs():
            self.solver.add_clause(
                [
                    -self._access_litterals("t", p1, self.Q - 1),
                    -self._access_litterals("t", p2, self.Q - 1),
                ]
            )

    def _cz_crown(self):
        for a, b in self.cz_tuples:
            for p in range(self.P):
                self.solver.add_clause(
                    [-self._access_litterals("x", a, p)]
                    + [
                        self._access_litterals("x", b, n)
                        for n in self.parameters.layout.cz_neighbours(p)
                    ]
                )

    def _create_clauses(self):
        self._init_solver()
        self._get_cz()
        self._at_least_one_spot()
        self._only_one_spot_per_qubit()
        self._at_most_one_qubit_per_sport()
        self._minimal_distance()
        self._cz_crown()

    def _enter(self):
        self._init_litterals()
        self._create_clauses()

    def _delete(self) -> None:
        if self.solver is not None:
            self.solver.delete()
            self.solver = None

    def solve(self) -> bool:
        self._has_solution = self.solver.solve()
        return self._has_solution

    def get_solution(self) -> list[int]:
        assert self._has_solution, "UNSAT does not have solution"
        model = self.solver.get_model()
        res = []
        for q in range(self.Q):
            for p in range(self.P):
                if model[self._access_litterals("x", q, p) - 1] > 0:
                    res.append(p)
                    break
        return res
