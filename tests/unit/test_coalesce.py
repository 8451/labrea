import uuid

import pytest

from labrea import Coalesce, Option
from labrea.types import EvaluationError, ValidationError


def test_no_default():
    coalesce = Coalesce(Option("A"), Option("B"), Option("C"))

    assert coalesce({"A": 1}) == 1
    assert coalesce({"B": 2}) == 2
    assert coalesce({"C": 3}) == 3
    assert coalesce({"A": 1, "C": 3}) == 1
    with pytest.raises(EvaluationError):
        coalesce({})

    coalesce.validate({"A": 1})
    with pytest.raises(ValidationError):
        coalesce.validate({})

    assert coalesce.keys({"A": 1}) == {"A"}
    assert coalesce.keys({"A": 1, "B": 2}) == {"A"}
    assert coalesce.keys({}) == set()


def test_with_default():
    default = uuid.uuid4()
    coalesce = Coalesce(Option("A"), default)

    assert coalesce({"A": 1}) == 1
    assert coalesce({}) == default

    coalesce.validate({"A": 1})
    coalesce.validate({})
