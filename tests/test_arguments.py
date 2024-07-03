import pytest

from labrea.arguments import Arguments, EvaluatableArgs, EvaluatableKwargs, arguments
from labrea.exceptions import KeyNotFoundError
from labrea.option import Option


def test_arguments():
    assert repr(Arguments(1, 2, 3)) == "Arguments(1, 2, 3)"
    assert repr(Arguments(a=1, b=2, c=3)) == "Arguments(a=1, b=2, c=3)"
    assert repr(Arguments(1, b=2)) == "Arguments(1, b=2)"
    assert repr(Arguments()) == "Arguments()"

    assert Arguments(1, b=2) == Arguments(1, b=2)
    assert Arguments(1, b=2) != Arguments(1, b=3)
    assert Arguments(1, b=2) != object()



def test_evaluatable_args():
    args = EvaluatableArgs(Option('A'), Option('B'), Option('C'))

    assert args.evaluate({'A': 1, 'B': 2, 'C': 3}) == (1, 2, 3)
    args.validate({'A': 1, 'B': 2, 'C': 3})
    with pytest.raises(KeyNotFoundError):
        args.validate({'A': 1, 'B': 2})
    assert args.keys({'A': 1, 'B': 2, 'C': 3}) == {'A', 'B', 'C'}
    with pytest.raises(KeyNotFoundError):
        args.keys({'A': 1, 'B': 2})
    assert args.explain() == {'A', 'B', 'C'}

    assert repr(args) == "EvaluatableArgs(Option('A'), Option('B'), Option('C'))"


def test_evaluatable_kwargs():
    kwargs = EvaluatableKwargs(a=Option('A'), b=Option('B'), c=Option('C'))

    assert kwargs.evaluate({'A': 1, 'B': 2, 'C': 3}) == {'a': 1, 'b': 2, 'c': 3}
    kwargs.validate({'A': 1, 'B': 2, 'C': 3})
    with pytest.raises(KeyNotFoundError):
        kwargs.validate({'A': 1, 'B': 2})
    assert kwargs.keys({'A': 1, 'B': 2, 'C': 3}) == {'A', 'B', 'C'}
    with pytest.raises(KeyNotFoundError):
        kwargs.keys({'A': 1, 'B': 2})
    assert kwargs.explain() == {'A', 'B', 'C'}

    assert repr(kwargs) == "EvaluatableKwargs(a=Option('A'), b=Option('B'), c=Option('C'))"


def test_evaluatable_arguments():
    args = arguments(Option('A'), b=Option('B'))

    assert args.evaluate({'A': 1, 'B': 2}) == Arguments(1, b=2)
    args.validate({'A': 1, 'B': 2})
    with pytest.raises(KeyNotFoundError):
        args.validate({'A': 1})
    assert args.keys({'A': 1, 'B': 2}) == {'A', 'B'}
    with pytest.raises(KeyNotFoundError):
        args.keys({'A': 1})
    assert args.explain() == {'A', 'B'}

    assert repr(args) == "EvaluatableParameters(Option('A'), b=Option('B'))"
