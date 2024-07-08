import pytest
from typing import List

from labrea import pipeline_step, Option, Value
from labrea.exceptions import EvaluationError
from labrea.pipeline import Pipeline, PipelineStep


@pipeline_step
def incr(x: float) -> float:
    return x + 1


@pipeline_step
def repeat(x: float, n: int = Option('N')) -> List[float]:
    return [x for _ in range(n)]


incr_then_repeat = incr + repeat


def test_types():
    assert isinstance(incr, PipelineStep)
    assert isinstance(repeat, PipelineStep)
    assert isinstance(incr_then_repeat, Pipeline)


def test_pipeline_valid():
    assert incr_then_repeat.evaluate({'N': 3})(1) == [2, 2, 2]
    incr_then_repeat.validate({'N': 3})
    assert incr_then_repeat.keys({'N': 3}) == {'N'}
    assert incr_then_repeat.explain({'N': 3}) == {'N'}


def test_pipeline_invalid():
    with pytest.raises(EvaluationError):
        incr_then_repeat.evaluate({})
    with pytest.raises(EvaluationError):
        incr_then_repeat.validate({})
    with pytest.raises(EvaluationError):
        incr_then_repeat.keys({})
    assert incr_then_repeat.explain() == {'N'}


def test_repr():
    assert repr(incr) == '<PipelineStep incr>'
    assert repr(incr_then_repeat) == '<Pipeline <PipelineStep incr> + <PipelineStep repeat>>'
    assert repr(Pipeline()) == '<Pipeline Identity>'


def test_iter():
    assert list(incr_then_repeat) == [incr, repeat]


def test_add():
    def decr(x: float) -> float:
        return x - 1

    assert list(incr + repeat) == [incr, repeat]
    assert list(incr + repeat + decr) == [incr, repeat, PipelineStep(Value(decr))]
    assert list(incr_then_repeat + incr_then_repeat) == [incr, repeat, incr, repeat]
    assert list(Pipeline() + incr) == list(incr + Pipeline()) == [incr]


def test_transformation():
    assert incr.transform(1) == 2
    assert list(repeat.transform(1, {'N': 3})) == [1, 1, 1]
    assert list(incr_then_repeat.transform(1, {'N': 3})) == [2, 2, 2]
