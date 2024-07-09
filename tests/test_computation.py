import pytest

from labrea.computation import Computation, ChainedEffect, CallbackEffect
from labrea.exceptions import EvaluationError
from labrea.option import Option
from labrea.pipeline import pipeline_step


def test_callback_effect():
    store = None

    @pipeline_step
    def store_value_add_a(value: int, a: int = Option('A')) -> None:
        nonlocal store
        store = value + a

    effect = CallbackEffect(store_value_add_a)

    assert effect.transform(1, {'A': 1}) is None
    assert store == 2
    effect.validate({'A': 1})
    assert effect.explain() == {'A'}
    assert repr(effect) == f"CallbackEffect({store_value_add_a!r})"

    with pytest.raises(EvaluationError):
        effect.transform(1, {})
    with pytest.raises(EvaluationError):
        effect.validate({})


def test_chained_effect():
    a = lambda x: None
    b = lambda x: None

    effect = ChainedEffect(CallbackEffect(a), CallbackEffect(b))

    assert effect.transform(1) is None
    effect.validate({})
    assert effect.explain() == set()
    assert repr(effect) == f"ChainedEffect(CallbackEffect(Value({a!r})), CallbackEffect(Value({b!r})))"


def test_computation():
    store = None

    @pipeline_step
    def store_value_add_a(value: int, a: int = Option('A')) -> None:
        nonlocal store
        store = value + a

    comp = Computation(Option('A'), CallbackEffect(store_value_add_a))

    assert comp.evaluate({'A': 1}) == 1
    assert store == 2
    comp.validate({'A': 1})
    assert comp.keys({'A': 1}) == {'A'}
    assert comp.explain() == {'A'}

    assert repr(comp) == f"Computation(Option('A'), CallbackEffect({store_value_add_a!r}))"
