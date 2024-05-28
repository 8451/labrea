import pytest

from labrea import Option, Template, dataset
from labrea.types import EvaluationError, ValidationError


@dataset
def b(b_: str = Option("B")) -> str:
    return b_


t = Template("{A.X} {:b:}", b=b)


def test_evaluate():
    assert t({"A": {"X": "Hello"}, "B": "World!"}) == "Hello World!"

    with pytest.raises(EvaluationError):
        t({"A": {"X": "Hello"}})

    with pytest.raises(EvaluationError):
        t({"B": "World!"})


def test_validate():
    t.validate({"A": {"X": "Hello"}, "B": "World!"})

    with pytest.raises(ValidationError):
        t.validate({"A": {"X": "Hello"}})

    with pytest.raises(ValidationError):
        t.validate({"B": "World!"})


def test_keys():
    assert t.keys({"A": {"X": "Hello"}, "B": "World!"}) == {"A.X", "B"}


def test_invalid_template():
    with pytest.raises(ValueError):
        Template("{A.X} {:b:}")

    with pytest.raises(ValueError):
        Template("{A.X} {:b:}", a="Unused")

    with pytest.warns(UserWarning):
        Template("{A.X} {:b:}", a="Unused", b=b)
