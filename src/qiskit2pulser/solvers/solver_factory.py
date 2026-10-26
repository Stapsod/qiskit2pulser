from qiskit2pulser.parameters.solver_parameters import SolverParameters
from qiskit2pulser.solvers.PySAT import PySAT
from qiskit2pulser.solvers.solver import Solver

available_solvers = {"pysat": PySAT}


def make_solver(parameters: SolverParameters) -> Solver:
    solver = available_solvers.get(parameters.type)
    if solver is None:
        raise ValueError(
            f"SolverParameters: the solver {parameters.type} is not supported yet. The supported solvers are {', '.join(available_solvers.keys())}"
        )
    return solver(parameters)
