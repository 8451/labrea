import pytest

from labrea import datasetclass, Option
from labrea.exceptions import KeyNotFoundError


@datasetclass
class X:
    a: int = Option('A')
    b: bool = True
    c: str = Option('C').apply(str)


@datasetclass
class X2:
    a: int = Option('A')
    b: bool = True
    c: str = Option('C').apply(str)


def test_evaluate():
    x = X({'A': 1, 'C': 3})

    assert x.a == 1
    assert x.b is True
    assert x.c == '3'

    with pytest.raises(KeyNotFoundError) as exc_info:
        X({'A': 1})
        assert exc_info.value.key == 'C'


def test_validate():
    X.validate({'A': 1, 'C': 3})

    with pytest.raises(KeyNotFoundError) as exc_info:
        X.validate({'A': 1})
        assert exc_info.value.key == 'C'


def test_keys():
    assert X.keys({'A': 1, 'C': 3}) == {'A', 'C'}

    with pytest.raises(KeyNotFoundError) as exc_info:
        X.keys({'A': 1})
        assert exc_info.value.key == 'C'


def test_explain():
    assert X.explain() == X.explain({'A': 1, 'C': 3}) == {'A', 'C'}


def test_repr():
    assert repr(X) == '<DatasetClass X>'
    opts = {'A': 1, 'C': 3}
    assert repr(X(opts)) == f'X({opts!r})'


def test_missing_default():
    with pytest.raises(ValueError):
        @datasetclass
        class Y:
            a: int = Option('A')
            b: bool
            c: str = Option('C').apply(str)


def test_eq():
    assert X({'A': 1, 'C': 3}) == X({'A': 1, 'C': 3})
    assert X({'A': 1, 'C': 3}) != X({'A': 1, 'C': 4})
    assert X({'A': 1, 'C': 3}) != X2({'A': 1, 'C': 3})


def test_inheritance():
    @datasetclass
    class Y(X):
        d: float = Option('D')

    y = Y({'A': 1, 'C': 3, 'D': 4.0})
    assert y.a == 1
    assert y.b is True
    assert y.c == '3'
    assert y.d == 4.0
