import pytest

from labrea import Switch
from labrea.types import EvaluationError


def test_dispatch():
    switch = Switch("X", {1: 1})

    with pytest.raises(EvaluationError):
        switch.evaluate({"X": []})


def test_has_default_prop():
    assert not Switch("X", {1: 1}).has_default
    assert Switch("X", {1: 1}, 10).has_default
