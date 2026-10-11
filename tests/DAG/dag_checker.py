from dataclasses import dataclass, field
from src.qiskit2pulser.utils.DAG import DAG, Node
from qiskit import QuantumCircuit


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

    def _get_all_nodes(self) -> set[Node]:
        res = set()

        def _aux(n: Node | None):
            if n is not None and n not in res:
                res.add(n)
                for s in n.successors.values():
                    _aux(s)

        for n in self.dag.entries:
            _aux(n)

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
