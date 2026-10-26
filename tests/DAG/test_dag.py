from tests.DAG.dag_checker import DAGChecker


def test_node_count(checker: DAGChecker):
    checker.check_node_count()


def test_qubit_chains(checker: DAGChecker):
    checker.check_qubit_chains()


def test_entries(checker: DAGChecker):
    checker.check_entries()


def test_bfs(checker: DAGChecker):
    checker.check_bfs()
