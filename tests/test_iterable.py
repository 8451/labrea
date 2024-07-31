import pytest

from labrea.iterable import Iter, Map
from labrea.conditional import switch
from labrea.exceptions import EvaluationError, InsufficientInformationError
from labrea.option import Option


def test_iter():
    i = Iter(Option('A'), 2)

    assert i.apply(list).evaluate({'A': 1}) == [1, 2]
    i.validate({'A': 1})
    assert i.keys({'A': 1}) == {'A'}
    assert i.explain() == {'A'}

    with pytest.raises(EvaluationError):
        i.apply(list).evaluate({})
    with pytest.raises(EvaluationError):
        i.validate({})
    with pytest.raises(EvaluationError):
        i.keys({})

    assert repr(i) == "Iter(Option('A'), Value(2))"


def test_iterate():
    i = Map(Option('A'), {'A': Option('B')})

    assert i.apply(list).evaluate({'B': [1, 2]}) == [({'A': 1}, 1), ({'A': 2}, 2)]
    assert i.values.apply(list).evaluate({'B': [1, 2]}) == [1, 2]
    i.validate({'B': [1, 2]})
    assert i.keys({'B': [1, 2]}) == {'B'}
    assert i.explain({'B': [1, 2]}) == {'B'}

    with pytest.raises(EvaluationError):
        i.apply(list).evaluate({})
    with pytest.raises(EvaluationError):
        i.validate({})
    with pytest.raises(EvaluationError):
        i.keys({})
    assert i.explain() == {'B'}

    assert repr(i) == "Iterate(Option('A'), {'A': Option('B')})"


def test_iterate_explain_insufficient_information():
    i = Map(switch(Option('A'), {'X': 1}), {'A': Option('B')})

    with pytest.raises(InsufficientInformationError):
        i.explain()
