import pytest

from labrea.application import FunctionApplication
from labrea import Value
from labrea.exceptions import KeyNotFoundError
from labrea.option import Option
from labrea.overload import Overloaded, overloaded


def test_overloaded():
    @overloaded(Option('A'))
    @FunctionApplication.lift
    def add(x: int = Option('X'), y: int = Option('Y')) -> int:
        return x + y

    @add.overload('dummy')
    def dummy_add():
        return 0

    with pytest.raises(TypeError):
        @add.overload()
        def _():
            pass

    assert add.evaluate({'X': 1, 'Y': 2}) == 3
    assert add.evaluate({'A': 'dummy'}) == 0

    add.validate({'X': 1, 'Y': 2})
    add.validate({'A': 'dummy'})
    with pytest.raises(KeyNotFoundError):
        add.validate({'X': 1})

    assert add.keys({'X': 1, 'Y': 2}) == {'X', 'Y'}
    assert add.keys({'A': 'dummy'}) == {'A'}
    with pytest.raises(KeyNotFoundError):
        add.keys({'X': 1})

    assert add.explain({'X': 1, 'Y': 2}) == {'X', 'Y'}
    assert add.explain({'A': 'dummy'}) == {'A'}
    assert add.explain() == {'X', 'Y'}


def test_repr():
    assert repr(Overloaded(Option('A'), {'X': Value(42)})) == "Overloaded(Option('A'), {'X': Value(42)})"
    assert repr(Overloaded(Option('A'), {'X': Value(42)}, default=43)) == "Overloaded(Option('A'), {'X': Value(42)}, Value(43))"

