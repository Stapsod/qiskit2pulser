from typing import Any


def make_config() -> dict[str, dict[str, Any]]:
    """Config used by the tests, independent of config.toml.

    A fresh dict on each call: the parameters keep a reference to it, and
    tests may change it (e.g. apply_opti).
    The 6 µm threshold sets the CZ error assumed by the end to end tests.
    """
    return {
        "compiler": {"apply_opti": True},
        "backend": {"type": "pulser"},
        "pulser": {"omega": 2.0, "step": 2.0, "threshold": 6.0},
        "SAT_solver": {"type": "pysat", "name": "cadical195"},
    }
