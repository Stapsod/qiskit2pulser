from typing import Callable

import pytest
import random
from qiskit import QuantumCircuit
from qiskit.circuit.library import get_standard_gate_name_mapping
from src.qiskit2pulser.qiskit_to_dag import _gate_types, QC_to_DAG
from src.qiskit2pulser.utils.DAG import DAG, Node


def apply_gate(qc: QuantumCircuit, gate: str, *qubits: int):
    getattr(qc, gate)(*qubits)


def get_all_nodes(d: DAG) -> set[Node]:
    res = set()

    def _aux(n: Node | None):
        if n is not None and n not in res:
            res.add(n)
            for s in list(n.successors.values()):
                _aux(s)

    for n in d.entries:
        _aux(n)

    return res


def get_gates(qc: QuantumCircuit):
    gates = [[] for _ in range(qc.num_qubits)]
    for g in qc.data:
        qubits = [qc.find_bit(q).index for q in g.qubits]
        for ind in qubits:
            gates[ind].append((g.operation.name, qubits))
    return gates


def get_successors_with_q(node: Node, q: int) -> Node | None:
    if q in node.successors:
        return node.successors[q]
    return None


def compare_dag_path_to_gates(
    entry: Node | None, gates: list[tuple[str, list[int]]], q: int
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
        entry = get_successors_with_q(entry, q)
        i += 1

    assert entry is None, (
        f"compare_dag_path_to_gates: entry expected to be None, not {entry}"
    )
    assert i == len_gates, (
        f"compare_dag_path_to_gates: for i, expected {len_gates}, got {i}"
    )
    return last_gate


@pytest.fixture
def generate_circuit_and_DAG() -> Callable[
    [int, int, list[str], int], tuple[QuantumCircuit, DAG]
]:
    def _generate(
        nb_qubits: int, nb_gates: int, gates: list[str], seed: int
    ) -> tuple[QuantumCircuit, DAG]:
        rng = random.Random(seed)
        qc = QuantumCircuit(nb_qubits)
        standard_gate_name_mapping = get_standard_gate_name_mapping()
        filtered_gates = list(
            filter(
                lambda g: standard_gate_name_mapping[g].num_qubits <= nb_qubits, gates
            )
        )
        if filtered_gates == []:
            raise ValueError("_generate: Filtered Gates set is empty.")

        for _ in range(nb_gates):
            gate = rng.choice(filtered_gates)
            num_qubits = standard_gate_name_mapping[gate].num_qubits

            apply_gate(
                qc,
                gate,
                *rng.sample(range(nb_qubits), num_qubits),
            )
        return (qc, QC_to_DAG(qc))

    return _generate


@pytest.mark.parametrize("seed", range(50))
def test_generator(generate_circuit_and_DAG, seed):
    qc, dag = generate_circuit_and_DAG(4, 5, list(_gate_types.keys()), seed)
    all_gates = get_all_nodes(dag)
    assert len(all_gates) == len(qc.data), (
        "test_generator: qc.data and dag does not have the same number of gates"
    )
    gates = get_gates(qc)
    for i in range(dag.num_qubits):
        last_gate = compare_dag_path_to_gates(dag.first_gate[i], gates[i], i)
        assert last_gate is dag.last_gate[i], (
            f"test_generator: dag.last_gate[i] does not match the last gate encountered. Last gate found = {last_gate}, dag.last_gate[i] = {dag.last_gate[i]}"
        )
    successors = {s for g in all_gates for s in g.successors.values()}
    assert set(dag.entries) == all_gates - successors, (
        f"test_generator: entries does not match the gates without predecessors. Expected {all_gates - successors}, got {dag.entries}"
    )
    assert len(set(dag.entries)) == len(dag.entries), (
        "test_generator: entries contains duplicated nodes."
    )
