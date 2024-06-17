from labrea.iterable import Iter
from labrea.evaluatable import Value
from labrea.option import Option


def test_iter():
    i = Iter(Option('A'), 2)

    assert i.apply(list).evaluate({'A': 1}) == [1, 2]
    i.validate({'A': 1})
    assert i.keys({'A': 1}) == {'A'}
    assert i.explain() == {'A'}

    assert repr(i) == "Iter(Option('A'), Value(2))"
