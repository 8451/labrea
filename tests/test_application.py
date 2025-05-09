from labrea import Option
from labrea.application import FunctionApplication, PartialApplication
from labrea.exceptions import EvaluationError, KeyNotFoundError
import pytest


def add(x: float, y: float) -> float:
    return x + y


def test_application():
    a = Option('A')
    b = Option('B')

    app = FunctionApplication(add, a, b)

    assert app.evaluate({'A': 1, 'B': 2}) == 3
    with pytest.raises(EvaluationError):
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


def test_partial_application():
    b = Option('B')

    app = PartialApplication(add, b)

    assert app.evaluate({'B': 2})(1) == 3
    with pytest.raises(EvaluationError):
        app.evaluate({})

    app.validate({'B': 2})
    with pytest.raises(KeyNotFoundError):
        app.validate({})

    assert app.keys({'B': 2}) == {'B'}
    with pytest.raises(KeyNotFoundError):
        app.keys({})

    assert app.explain() == {'B'}

    assert repr(app) == "PartialApplication(add, Option('B'))"


def test_lift_partial():
    def some(a: float, b: float = Option('B')) -> float:
        return a + b

    def none(a: float, b: float) -> float:
        return a + b

    def all(a: float = Option('A'), b: float = Option('B')) -> float:
        return a + b

    assert PartialApplication.lift(some).evaluate({'B': 2})(1) == 3
    assert PartialApplication.lift(some).evaluate({'B': 2})(a=1, b=3) == 4
    assert PartialApplication.lift(some, b=Option('C')).evaluate({'C': 4})(1) == 5

    assert PartialApplication.lift(none).evaluate({})(1, 2) == 3

    assert PartialApplication.lift(all).evaluate({'A': 1, 'B': 2})() == 3

    @PartialApplication.lift
    def good_deco(a: float, b: float = Option('B')) -> float:
        return a + b

    assert good_deco.evaluate({'B': 2})(1) == 3

    @PartialApplication.lift(b=Option('B'))
    def good_deco_kwargs(a: float, b: float = Option('X')) -> float:
        return a + b

    assert good_deco_kwargs.evaluate({'B': 2})(1) == 3
