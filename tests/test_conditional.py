from labrea.conditional import switch, SwitchError, case, CaseWhenError
from labrea.exceptions import KeyNotFoundError, InsufficientInformationError
from labrea.option import Option
import pytest


def test_switch():
    s = switch(Option('A'), {'X': 42, 'Y': Option('Z')})

    assert s({'A': 'X'}) == 42
    assert s({'A': 'Y', 'Z': 43}) == 43
    with pytest.raises(KeyNotFoundError):
        s.evaluate({})
    with pytest.raises(KeyNotFoundError):
        s.evaluate({'A': 'Y'})
    with pytest.raises(SwitchError):
        s.evaluate({'A': 'Z'})

    s.validate({'A': 'X'})
    s.validate({'A': 'Y', 'Z': 43})
    with pytest.raises(KeyNotFoundError):
        s.validate({})
    with pytest.raises(KeyNotFoundError):
        s.validate({'A': 'Y'})
    with pytest.raises(SwitchError):
        s.validate({'A': 'Z'})

    assert s.keys({'A': 'X'}) == {'A'}
    assert s.keys({'A': 'Y', 'Z': 43}) == {'A', 'Z'}
    with pytest.raises(KeyNotFoundError):
        s.keys({})
    with pytest.raises(KeyNotFoundError):
        s.keys({'A': 'Y'})
    with pytest.raises(SwitchError):
        s.keys({'A': 'Z'})

    assert s.explain({'A': 'X'}) == {'A'}
    assert s.explain({'A': 'Y', 'Z': 43}) == {'A', 'Z'}
    with pytest.raises(InsufficientInformationError):
        s.explain({})
    assert s.explain({'A': 'Y'}) == {'A', 'Z'}
    with pytest.raises(InsufficientInformationError):
        assert s.explain({'A': 'Z'}) == {'A'}

    assert repr(s) == "switch(Option('A'), {'X': Value(42), 'Y': Option('Z')})"
    assert (
        repr(switch(Option('A'), {'X': 42, 'Y': Option('Z')}, 43)) ==
        "switch(Option('A'), {'X': Value(42), 'Y': Option('Z')}, Value(43))"
    )

    assert switch('A', {'X': 1})({'A': 'X'}) == 1


def test_case_when():
    c = case(Option('A')).when(
        lambda x: x == 'X',
        42
    ).when(
        lambda x: x == 'Y',
        Option('Z')
    ).otherwise(43)

    assert c({'A': 'X'}) == 42
    assert c({'A': 'Y', 'Z': 44}) == 44
    assert c({'A': 'Z'}) == 43
    with pytest.raises(KeyNotFoundError):
        c.evaluate({})
    with pytest.raises(KeyNotFoundError):
        c.evaluate({'A': 'Y'})

    c.validate({'A': 'X'})
    c.validate({'A': 'Y', 'Z': 44})
    c.validate({'A': 'Z'})
    with pytest.raises(KeyNotFoundError):
        c.validate({})
    with pytest.raises(KeyNotFoundError):
        c.validate({'A': 'Y'})
    c.validate({'A': 'Z'})

    assert c.keys({'A': 'X'}) == {'A'}
    assert c.keys({'A': 'Y', 'Z': 44}) == {'A', 'Z'}
    assert c.keys({'A': 'Z'}) == {'A'}
    with pytest.raises(KeyNotFoundError):
        c.keys({})
    with pytest.raises(KeyNotFoundError):
        c.keys({'A': 'Y'})
    assert c.keys({'A': 'Z'}) == {'A'}

    assert c.explain({'A': 'X'}) == {'A'}
    assert c.explain({'A': 'Y', 'Z': 44}) == {'A', 'Z'}
    assert c.explain({'A': 'Z'}) == {'A'}
    with pytest.raises(InsufficientInformationError):
        c.explain({})
    assert c.explain({'A': 'Y'}) == {'A', 'Z'}
    assert c.explain({'A': 'Z'}) == {'A'}


def test_case_when_no_default():
    c = case(Option('A')).when(
        lambda x: x == 'X',
        42
    ).when(
        lambda x: x == 'Y',
        Option('Z')
    )

    assert c({'A': 'X'}) == 42
    assert c({'A': 'Y', 'Z': 44}) == 44
    with pytest.raises(CaseWhenError):
        c({'A': 'Z'})
    with pytest.raises(KeyNotFoundError):
        c.evaluate({})

    c.validate({'A': 'X'})
    c.validate({'A': 'Y', 'Z': 44})
    with pytest.raises(CaseWhenError):
        c.validate({'A': 'Z'})
    with pytest.raises(KeyNotFoundError):
        c.validate({})

    assert c.keys({'A': 'X'}) == {'A'}
    assert c.keys({'A': 'Y', 'Z': 44}) == {'A', 'Z'}
    with pytest.raises(CaseWhenError):
        c.keys({'A': 'Z'})
    with pytest.raises(KeyNotFoundError):
        c.keys({})

    assert c.explain({'A': 'X'}) == {'A'}
    assert c.explain({'A': 'Y', 'Z': 44}) == {'A', 'Z'}
    with pytest.raises(InsufficientInformationError):
        c.explain({'A': 'Z'})
    with pytest.raises(InsufficientInformationError):
        c.explain({})
