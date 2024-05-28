import pytest
from functional_pypelines.validator import ValidationError

from labrea import LabreaPipeline, Option, dataset
from labrea.pipelines import validator
from labrea.types import EvaluationError


@dataset
def double_a(a: int = Option("A").result) -> int:
    return a * 2


@LabreaPipeline.step
def add_double_a(x: int, dbl_a: int = double_a.result) -> int:
    return x + dbl_a


@LabreaPipeline.step
def divide(x: int, divisor: int = Option("DIVISOR").result) -> float:
    return x / divisor


pipeline = add_double_a >> divide >> LabreaPipeline.unwrap


def test_valid_input():
    options = {"A": 4, "DIVISOR": 3}
    validator.validate(pipeline, 1, options)
    assert pipeline(1, options) == 3


def test_invalid_input():
    with pytest.raises(ValidationError):
        validator.validate(pipeline, 1, {})
    with pytest.raises(ValidationError):
        validator.validate(pipeline, 1, {"A": 4})
    with pytest.raises(ValidationError):
        validator.validate(pipeline, 1, {"DIVISOR": 3})
    with pytest.raises(EvaluationError):
        pipeline(1, {})


def test_warning():
    with pytest.warns():

        @LabreaPipeline.step
        def default_argument(x: int = 1, y: int = 2) -> int:
            return x + y


def test_no_value():
    @LabreaPipeline.step
    def no_default_value(_, x: int = Option("X").result):
        return x

    assert no_default_value(options={"X": 1}).value == 1
