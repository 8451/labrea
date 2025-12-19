import pytest

from labrea import ENV, Value
from labrea.exceptions import EvaluationError


def test_env_set(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test setting and getting environment variables using ENV."""
    monkeypatch.setenv("TEST_ENV_VAR", "test_value")
    env_var = ENV.TEST_ENV_VAR
    assert env_var.evaluate({}) == "test_value"


def test_env_missing(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test behavior when environment variable is missing."""
    monkeypatch.delenv("MISSING_ENV_VAR", raising=False)
    env_var = ENV.MISSING_ENV_VAR
    with pytest.raises(EvaluationError) as exc_info:
        _ = env_var.evaluate({})
    assert "Environment variable 'MISSING_ENV_VAR' not found" in str(exc_info.value)


def test_env_or_operator(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test the use of the | operator with ENV."""
    monkeypatch.delenv("OPTIONAL_ENV_VAR", raising=False)
    env_var = ENV.OPTIONAL_ENV_VAR | "default_value"
    assert env_var.evaluate({}) == "default_value"

    env_var = ENV.OPTIONAL_ENV_VAR | Value("another_default")
    assert env_var.evaluate({}) == "another_default"

    monkeypatch.setenv("OPTIONAL_ENV_VAR", "set_value")
    env_var = ENV.OPTIONAL_ENV_VAR | "default_value"
    assert env_var.evaluate({}) == "set_value"
