import pytest

from labrea.computation import Computation, ChainedEffect, CallbackEffect
from labrea.evaluatable import EvaluationError
from labrea.option import Option
from labrea.pipeline import pipeline_step


def test_chained_effect():
    incr = lambda x: x + 1
    double = lambda x: x * 2

    effect = ChainedEffect(CallbackEffect(incr), CallbackEffect(double))

    assert effect(1) == 4
    effect.validate({})
    assert effect.explain() == set()
    assert repr(effect) == f"ChainedEffect(CallbackEffect(Value({incr!r})), CallbackEffect(Value({double!r})))"


def test_callback_effect():
    @pipeline_step
    def add_a(value: int, a: int = Option('A')) -> int:
        return value + a

    effect = CallbackEffect(add_a)

    assert effect(1, {'A': 1}) == 2
    effect.validate({'A': 1})
    assert effect.explain() == {'A'}
    assert repr(effect) == f"CallbackEffect({add_a!r})"

    with pytest.raises(EvaluationError):
        effect(1, {})
    with pytest.raises(EvaluationError):
        effect.validate({})


def test_computation():
    incr = lambda x: x + 1
    comp = Computation(Option('A'), CallbackEffect(incr))

    assert comp.evaluate({'A': 1}) == 2
    comp.validate({'A': 1})
    assert comp.keys({'A': 1}) == {'A'}
    assert comp.explain() == {'A'}

    assert repr(comp) == f"Computation(Option('A'), CallbackEffect(Value({incr!r})))"
