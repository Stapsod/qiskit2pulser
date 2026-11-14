from typing import Any


def make_config() -> dict[str, dict[str, Any]]:
    """Config used by the tests, independent of config.toml.

    A fresh dict on each call, since the parameters keep a reference to it.
    The 6 µm threshold sets the CZ error assumed by the end to end tests.
    """
    return {
        "backend": {"type": "pulser"},
        "pulser": {"omega": 2.0, "step": 2.0, "threshold": 6.0},
        "SAT_solver": {"type": "pysat", "name": "cadical195"},
    }
