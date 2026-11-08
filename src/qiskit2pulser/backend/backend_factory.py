import tomllib
from pathlib import Path

from qiskit2pulser.backend.backend import Backend
from qiskit2pulser.backend.pulser_backend import PulserBackend
from qiskit2pulser.parameters.backend_parameters import BackendParameters
from qiskit2pulser.parameters.pulser_parameters import PulserParameters

available_backend = {"pulser": PulserBackend}
available_backend_parameters = {"pulser": PulserParameters}


def make_backend_parameters(config_path: str | Path) -> BackendParameters:
    with open(config_path, "rb") as f:
        backend_type = tomllib.load(f)["backend"]["type"]
    parameters = available_backend_parameters.get(backend_type)
    if parameters is None:
        raise ValueError(
            f"BackendParameters: the backend {backend_type} is not supported yet. The supported backend are {', '.join(available_backend_parameters.keys())}"
        )
    return parameters(config_path)


def make_backend(parameters: BackendParameters) -> Backend:
    backend = available_backend.get(parameters.type)
    if backend is None:
        raise ValueError(
            f"BackendParameters: the backend {parameters.type} is not supported yet. The supported backend are {', '.join(available_backend.keys())}"
        )
    return backend(parameters)
