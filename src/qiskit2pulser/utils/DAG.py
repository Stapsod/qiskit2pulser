from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field
from itertools import count

from src.qiskit2pulser.utils.Gate import Gate


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

    def to_dot_string(self):
        res = "digraph DAG\n{\n\trankdir=LR;\n"
        decl = ""
        edges = ""
        gates = set()

        for e in self.entries:
            act = [e]
            while act != []:
                node = act.pop(0)
                if node.name not in gates:
                    gates.add(node.name)
                    decl += f'\t{node.name} [label="{node.name}", shape=square];\n'
                    for succ in node.successors.values():
                        act.append(succ)
                        edges += f"\t{node.name} -> {succ.name};\n"

        for q in range(self.num_qubits):
            name = f"q{q}"
            decl += f'\t{name} [label="{name}", shape=circle];\n'
            if self.first_gate[q] is not None:
                edges += f"\t{name} -> {self.first_gate[q].name} [style=dashed];\n"

        res += decl + edges + "}\n"
        return res
