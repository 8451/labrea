from labrea.computation import Computation, UnvalidatedEffect
from labrea.option import Option


def test_computation():
    incr = lambda x: x + 1
    comp = Computation(Option('A'), UnvalidatedEffect(incr))

    assert comp.evaluate({'A': 1}) == 2
    comp.validate({'A': 1})
    assert comp.keys({'A': 1}) == {'A'}
    assert comp.explain() == {'A'}

    assert repr(comp) == f"Computation(Option('A'), UnvalidatedEffect({incr!r}))"
