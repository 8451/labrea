from labrea.computation import Computation, UnvalidatedEffect, ChainedEffect, CallbackEffect
from labrea.option import Option


def test_unvalidated_effect():
    incr = lambda x: x + 1
    effect = UnvalidatedEffect(incr)

    assert effect(1) == 2
    effect.validate({})
    assert effect.explain() == set()
    assert repr(effect) == f"UnvalidatedEffect({incr!r})"


def test_chained_effect():
    incr = lambda x: x + 1
    double = lambda x: x * 2

    effect = ChainedEffect(UnvalidatedEffect(incr), UnvalidatedEffect(double))

    assert effect(1) == 4
    effect.validate({})
    assert effect.explain() == set()
    assert repr(effect) == f"ChainedEffect(UnvalidatedEffect({incr!r}), UnvalidatedEffect({double!r}))"


def test_callback_effect():
    def add_a(value, options):
        return value + options['A']

    effect = CallbackEffect(add_a)

    assert effect(1, {'A': 1}) == 2
    effect.validate({'A': 1})
    assert effect.explain() == set()
    assert repr(effect) == f"CallbackEffect({add_a!r})"


def test_computation():
    incr = lambda x: x + 1
    comp = Computation(Option('A'), UnvalidatedEffect(incr))

    assert comp.evaluate({'A': 1}) == 2
    comp.validate({'A': 1})
    assert comp.keys({'A': 1}) == {'A'}
    assert comp.explain() == {'A'}

    assert repr(comp) == f"Computation(Option('A'), UnvalidatedEffect({incr!r}))"
