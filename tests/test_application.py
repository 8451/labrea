from labrea.application import FunctionApplication
from labrea.option import Option
from labrea.evaluatable import KeyNotFoundError
import pytest


def add(x: float, y: float) -> float:
    return x + y


def test_application():
    a = Option('A')
    b = Option('B')

    app = FunctionApplication(add, a, b)

    assert app.evaluate({'A': 1, 'B': 2}) == 3
    with pytest.raises(KeyNotFoundError):
        app.evaluate({'A': 1})

    app.validate({'A': 1, 'B': 2})
    with pytest.raises(KeyNotFoundError):
        app.validate({'A': 1})

    assert app.keys({'A': 1, 'B': 2}) == {'A', 'B'}
    with pytest.raises(KeyNotFoundError):
        app.keys({'A': 1})

    assert app.explain() == {'A', 'B'}

    assert repr(app) == "FunctionApplication(add, Option('A'), Option('B'))"


def test_lift():
    def good(a: float = Option('A'), b: float = Option('B')) -> float:
        return a + b

    def bad(a: float, b: float) -> float:
        return a + b

    assert FunctionApplication.lift(good).evaluate({'A': 1, 'B': 2}) == 3

    with pytest.raises(TypeError):
        FunctionApplication.lift(bad)

    assert FunctionApplication.lift(bad, a=Option('A'), b=Option('B')).evaluate({'A': 1, 'B': 2}) == 3

    @FunctionApplication.lift
    def good_deco(a: float = Option('A'), b: float = Option('B')) -> float:
        return a + b

    assert good_deco.evaluate({'A': 1, 'B': 2}) == 3

    @FunctionApplication.lift(a=Option('A'), b=Option('B'))
    def good_deco_kwargs(a: float, b: float = Option('X')) -> float:
        return a + b

    assert good_deco_kwargs.evaluate({'A': 1, 'B': 2}) == 3
