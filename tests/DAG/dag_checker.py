import re
from collections import Counter
from dataclasses import dataclass, field

from qiskit import QuantumCircuit

from src.qiskit2pulser.DAG.DAG import DAG, Node


@dataclass
class DAGChecker:
    qc: QuantumCircuit
    dag: DAG
    all_nodes: set[Node] = field(init=False)
    all_successors: set[Node] = field(init=False)
    gates_per_qubits: list[list[tuple[str, list[int]]]] = field(init=False)

    def __post_init__(self):
        self.all_nodes = self._get_all_nodes()
        self.all_successors = {s for g in self.all_nodes for s in g.successors.values()}
        self.gates_per_qubits = self._get_gates()

    def check_node_count(self):
        assert len(self.all_nodes) == len(self.qc.data), (
            "DAGChecker.check_node_count: qc.data and dag does not have the same number of gates"
        )

    def check_qubit_chains(self):
        for i in range(self.dag.num_qubits):
            last_gate = self._compare_dag_path_to_gates(
                self.dag.first_gate[i], self.gates_per_qubits[i], i
            )
            assert last_gate is self.dag.last_gate[i], (
                f"DAGChecker.check_qubit_chains: dag.last_gate[i] does not match the last gate encountered. Last gate found = {last_gate}, dag.last_gate[i] = {self.dag.last_gate[i]}"
            )

    def check_entries(self):
        assert set(self.dag.entries) == self.all_nodes - self.all_successors, (
            f"DAGChecker.check_entries: entries does not match the gates without predecessors. Expected {self.all_nodes - self.all_successors}, got {self.dag.entries}"
        )
        assert len(set(self.dag.entries)) == len(self.dag.entries), (
            "DAGChecker.check_entries: entries contains duplicated nodes."
        )

    def check_bfs(self):
        visited = []
        self.dag.bfs(visited.append)
        assert len(set(visited)) == len(visited), (
            "DAGChecker.check_bfs: bfs visited some nodes more than once."
        )
        assert len(visited) == len(self.qc.data), (
            f"DAGChecker.check_bfs: expected {len(self.qc.data)} visited nodes, got {len(visited)}"
        )
        assert set(visited) == self.all_nodes, (
            f"DAGChecker.check_bfs: visited nodes do not match the dag nodes. Missing {self.all_nodes - set(visited)}, unexpected {set(visited) - self.all_nodes}"
        )

    def check_dot_string(self):
        dot = self.dag.to_dot_string()
        declared = re.findall(r"^\t(\w+) \[", dot, re.MULTILINE)
        edges = Counter(re.findall(r"^\t(\w+) -> (\w+);$", dot, re.MULTILINE))
        dashed = Counter(
            re.findall(r"^\t(\w+) -> (\w+) \[style=dashed\];$", dot, re.MULTILINE)
        )

        qubits = [f"q{q}" for q in range(self.dag.num_qubits)]
        expected_declared = [n.name for n in self.all_nodes] + qubits
        assert Counter(declared) == Counter(expected_declared), (
            f"DAGChecker.check_dot_string: declared nodes do not match. Expected {sorted(expected_declared)}, got {sorted(declared)}"
        )

        # One edge per qubit wire: two gates sharing several qubits are linked several times
        expected_edges = Counter(
            (n.name, s.name) for n in self.all_nodes for s in n.successors.values()
        )
        assert edges == expected_edges, (
            f"DAGChecker.check_dot_string: edges do not match. Missing {expected_edges - edges}, unexpected {edges - expected_edges}"
        )

        expected_dashed = Counter(
            (f"q{q}", g.name)
            for q, g in enumerate(self.dag.first_gate)
            if g is not None
        )
        assert dashed == expected_dashed, (
            f"DAGChecker.check_dot_string: qubit edges do not match. Missing {expected_dashed - dashed}, unexpected {dashed - expected_dashed}"
        )

    def _get_all_nodes(self) -> set[Node]:
        res = set()
        stack = list(self.dag.entries)
        while stack:
            n = stack.pop()
            if n not in res:
                res.add(n)
                stack.extend(n.successors.values())

        return res

    def _get_gates(self):
        gates = [[] for _ in range(self.qc.num_qubits)]
        for g in self.qc.data:
            qubits = [self.qc.find_bit(q).index for q in g.qubits]
            for ind in qubits:
                gates[ind].append((g.operation.name, qubits))
        return gates

    def _compare_dag_path_to_gates(
        self, entry: Node | None, gates: list[tuple[str, list[int]]], q: int
    ) -> Node | None:
        i = 0
        len_gates = len(gates)
        last_gate = None
        while entry is not None and i < len_gates:
            assert entry.gate.symbol == gates[i][0], (
                f"compare_dag_path_to_gates: expected {gates[i][0]}, got {entry.gate.symbol}"
            )
            assert entry.gate.qubits == gates[i][1], (
                f"compare_dag_path_to_gates: expected {gates[i][1]}, got {entry.gate.qubits}"
            )
            last_gate = entry
            entry = entry.successors.get(q)
            i += 1

        assert entry is None, (
            f"compare_dag_path_to_gates: entry expected to be None, not {entry}"
        )
        assert i == len_gates, (
            f"compare_dag_path_to_gates: for i, expected {len_gates}, got {i}"
        )
        return last_gate
