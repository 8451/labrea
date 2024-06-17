from labrea.coalesce import Coalesce, CoalesceError
from labrea.option import Option
from labrea.conditional import switch
from labrea.evaluatable import InsufficientInformationError
import pytest


def test_coalesce():
    a = Option('A')
    b = Option('V')

    c = Coalesce(a, b)

    assert c({'A': 'Hello'}) == 'Hello'
    assert c({'V': 'World!'}) == 'World!'
    assert c({'A': 'Hello', 'V': 'World!'}) == 'Hello'
    assert c({'V': 'World!', 'C': 'foo'}) == 'World!'

    with pytest.raises(CoalesceError):
        c({})

    with pytest.raises(CoalesceError):
        c.validate({})

    with pytest.raises(CoalesceError):
        c.keys({})

    assert c.explain() == {'A'}

    with pytest.raises(InsufficientInformationError):
        Coalesce(switch(Option('A'), {1: True})).explain({'A': 2})


def test_repr():
    assert repr(Coalesce(Option('A'), Option('V'))) == "Coalesce(Option('A'), Option('V'))"


def test_init():
    with pytest.raises(TypeError):
        Coalesce()
