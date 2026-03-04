"""Pytest configuration for evaluation tests."""

import pytest


def pytest_addoption(parser: pytest.Parser) -> None:
    parser.addoption(
        "--model-id",
        action="store",
        default="claude-sonnet-4-6",
        help="Model ID for evaluation (default: claude-sonnet-4-6)",
    )
    parser.addoption(
        "--eval-mode",
        action="store",
        default="live",
        choices=["live", "mock"],
        help="Evaluation mode: live (real LLMs) or mock (saved responses)",
    )
    parser.addoption(
        "--judge-model",
        action="store",
        default="claude-opus-4-6",
        help="Model for LLM-as-Judge semantic evaluation (default: claude-opus-4-6)",
    )


@pytest.fixture
def eval_model_id(request: pytest.FixtureRequest) -> str:
    return request.config.getoption("--model-id")


@pytest.fixture
def eval_mode(request: pytest.FixtureRequest) -> str:
    return request.config.getoption("--eval-mode")


@pytest.fixture
def judge_model(request: pytest.FixtureRequest) -> str:
    return request.config.getoption("--judge-model")
