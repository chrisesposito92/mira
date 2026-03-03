"""Evaluation example registry — provides ALL_EXAMPLES and get_example() lookup."""

from evals.datasets.app_hosting import APP_HOSTING
from evals.datasets.base import EvalExample
from evals.datasets.candidate_checks import CANDIDATE_CHECKS
from evals.datasets.cloud_storage import CLOUD_STORAGE

ALL_EXAMPLES: list[EvalExample] = [
    CLOUD_STORAGE,
    APP_HOSTING,
    CANDIDATE_CHECKS,
]

_BY_NAME: dict[str, EvalExample] = {e.name: e for e in ALL_EXAMPLES}


def get_example(name: str) -> EvalExample:
    """Look up an evaluation example by name.

    Args:
        name: Short identifier (e.g. "cloud_storage", "app_hosting", "candidate_checks").

    Returns:
        The matching EvalExample.

    Raises:
        KeyError: If no example with that name exists.
    """
    if name not in _BY_NAME:
        available = ", ".join(sorted(_BY_NAME.keys()))
        raise KeyError(f"Unknown example '{name}'. Available: {available}")
    return _BY_NAME[name]
