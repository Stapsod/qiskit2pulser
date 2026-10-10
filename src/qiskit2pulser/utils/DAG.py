from __future__ import annotations
from dataclasses import dataclass, field

from src.qiskit2pulser.utils.Gate import Gate


@dataclass(eq=False)
class Node:
    gate: Gate
    successors: list[Node] = field(default_factory=list)

    def add_successors(self, node: Node):
        self.successors.append(node)


@dataclass
class DAG:
    num_qubits: int
    entries: list[Node] = field(default_factory=list)
    last_gate: list[Node | None] = field(init=False)
    first_gate: list[Node | None] = field(init=False)

    def __post_init__(self):
        self.last_gate = [None] * self.num_qubits
        self.first_gate = [None] * self.num_qubits

    def add_gate(self, gate: Gate) -> None:
        node = Node(gate)
        pred = set()
        for q in gate.qubits:
            last = self.last_gate[q]
            if last is not None:
                pred.add(last)
            else:
                self.first_gate[q] = node

        if not pred:
            self.entries.append(node)

        for p in pred:
            p.add_successors(node)
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
                if node.gate.name not in gates:
                    gates.add(node.gate.name)
                    decl += f'\t{node.gate.name} [label="{node.gate.name}", shape=square];\n'
                    for succ in node.successors:
                        act.append(succ)
                        edges += f"\t{node.gate.name} -> {succ.gate.name};\n"

        for q in range(self.num_qubits):
            name = f"q{q}"
            decl += f'\t{name} [label="{name}", shape=circle];\n'
            if self.first_gate[q] is not None:
                edges += f"\t{name} -> {self.first_gate[q].gate.name} [style=dashed];\n"

        res += decl + edges + "}\n"
        return res
