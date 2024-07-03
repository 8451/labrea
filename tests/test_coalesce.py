from labrea.coalesce import Coalesce
from labrea.option import Option
from labrea.exceptions import KeyNotFoundError
import pytest


def test_coalesce():
    a = Option('A')
    b = Option('B')

    c = Coalesce(a, b)

    assert c({'A': 'Hello'}) == 'Hello'
    assert c({'B': 'World!'}) == 'World!'
    assert c({'A': 'Hello', 'B': 'World!'}) == 'Hello'
    assert c({'B': 'World!', 'C': 'foo'}) == 'World!'

    with pytest.raises(KeyNotFoundError):
        c({})

    with pytest.raises(KeyNotFoundError):
        c.validate({})

    with pytest.raises(KeyNotFoundError):
        c.keys({})

    assert c.explain() == {'B'}


def test_repr():
    assert repr(Coalesce(Option('A'), Option('B'))) == "Coalesce(Option('A'), Option('B'))"


def test_init():
    with pytest.raises(TypeError):
        Coalesce()
