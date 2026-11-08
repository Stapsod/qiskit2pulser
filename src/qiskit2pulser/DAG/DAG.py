from __future__ import annotations

from collections import defaultdict, deque
from dataclasses import dataclass, field
from itertools import count

from qiskit2pulser.DAG.Gate import Gate


@dataclass(eq=False)
class Node:
    gate: Gate
    name: str
    successors: dict[int, Node] = field(default_factory=dict, repr=False)

    def add_successors(self, node: Node, q: int):
        self.successors[q] = node


@dataclass
class DAG:
    num_qubits: int
    entries: list[Node] = field(default_factory=list)
    last_gate: list[Node | None] = field(init=False)
    first_gate: list[Node | None] = field(init=False)
    _counters: defaultdict[str, count] = field(
        default_factory=lambda: defaultdict(count), init=False, repr=False
    )

    def __post_init__(self):
        self.last_gate = [None] * self.num_qubits
        self.first_gate = [None] * self.num_qubits

    def add_gate(self, gate: Gate) -> None:
        node = Node(gate, f"{gate.symbol}{next(self._counters[gate.symbol])}")
        has_pred = False
        for q in gate.qubits:
            last = self.last_gate[q]
            if last is not None:
                last.add_successors(node, q)
                has_pred = True
            else:
                self.first_gate[q] = node

        if not has_pred:
            self.entries.append(node)

        for q in gate.qubits:
            self.last_gate[q] = node

    def bfs(self, f):
        gates = set()

        queue = deque(self.entries)
        while queue:
            node = queue.popleft()
            if node.name not in gates:
                gates.add(node.name)
                f(node)
                for succ in node.successors.values():
                    queue.append(succ)

    def topological(self, f):
        """Call f on every node, each one after all its predecessors (Kahn)."""
        # One edge per qubit wire, counted and consumed the same way
        indegree = defaultdict(int)

        def count(node: Node):
            for succ in node.successors.values():
                indegree[succ] += 1

        self.bfs(count)

        queue = deque(self.entries)
        while queue:
            node = queue.popleft()
            f(node)
            for succ in node.successors.values():
                indegree[succ] -= 1
                if indegree[succ] == 0:
                    queue.append(succ)

    def to_dot_string(self):
        res = "digraph DAG\n{\n\trankdir=LR;\n"
        decl_l = []
        edges_l = []

        def use_node(node: Node):
            decl_l.append(f'\t{node.name} [label="{node.name}", shape=square];\n')
            for succ in node.successors.values():
                edges_l.append(f"\t{node.name} -> {succ.name};\n")

        self.bfs(use_node)

        decl = "".join(decl_l)
        edges = "".join(edges_l)

        for q in range(self.num_qubits):
            name = f"q{q}"
            decl += f'\t{name} [label="{name}", shape=circle];\n'
            if self.first_gate[q] is not None:
                edges += f"\t{name} -> {self.first_gate[q].name} [style=dashed];\n"

        res += decl + edges + "}\n"
        return res

    def reduce_unitary_gate(self) -> None:
        for qi in range(self.num_qubits):
            kept: list[Node] = []
            n = self.first_gate[qi]
            while n is not None:
                suc = n.successors.get(qi)
                if (
                    kept
                    and len(n.gate.qubits) == 1
                    and kept[-1].gate.symbol == n.gate.symbol
                ):
                    self._remove_pair(kept.pop(), suc, kept[-1] if kept else None, qi)
                else:
                    kept.append(n)
                n = suc

    def _remove_pair(
        self, first: Node, after: Node | None, before: Node | None, q: int
    ) -> None:
        if before is not None:
            if after is not None:
                before.successors[q] = after
            else:
                del before.successors[q]
        else:
            self.first_gate[q] = after
            self.entries.remove(first)
            if after is not None and all(
                self.first_gate[w] is after for w in after.gate.qubits
            ):
                self.entries.append(after)
        if after is None:
            self.last_gate[q] = before
