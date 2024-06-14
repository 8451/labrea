from labrea.conditional import switch, SwitchError
from labrea.evaluatable import Value, InsufficientInformationError, KeyNotFoundError
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
        print(s.explain({'A': 'Z'}))

