import pytest

from labrea.application import FunctionApplication
from labrea import Value
from labrea.exceptions import KeyNotFoundError
from labrea.option import Option
from labrea.overload import Overloaded


def test_overloaded():
    @FunctionApplication.lift
    def add(x: int = Option('X'), y: int = Option('Y')) -> int:
        return x + y

    overloads = Overloaded(Option('A'), {}, default=add)

    @FunctionApplication.lift
    def dummy_add():
        return 0

    overloads.register('dummy', dummy_add)

    assert overloads.evaluate({'X': 1, 'Y': 2}) == 3
    assert overloads.evaluate({'A': 'dummy'}) == 0

    overloads.validate({'X': 1, 'Y': 2})
    overloads.validate({'A': 'dummy'})
    with pytest.raises(KeyNotFoundError):
        overloads.validate({'X': 1})

    assert overloads.keys({'X': 1, 'Y': 2}) == {'X', 'Y'}
    assert overloads.keys({'A': 'dummy'}) == {'A'}
    with pytest.raises(KeyNotFoundError):
        overloads.keys({'X': 1})

    assert overloads.explain({'X': 1, 'Y': 2}) == {'X', 'Y'}
    assert overloads.explain({'A': 'dummy'}) == {'A'}
    assert overloads.explain() == {'X', 'Y'}


def test_repr():
    assert repr(Overloaded(Option('A'), {'X': Value(42)})) == "Overloaded(Option('A'), {'X': Value(42)})"
    assert repr(Overloaded(Option('A'), {'X': Value(42)}, default=43)) == "Overloaded(Option('A'), {'X': Value(42)}, Value(43))"

