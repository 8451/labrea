import pytest

from labrea import Option
from labrea.types import ValidationError


def test_templating():
    opt = Option("C", "{A.X} {B}")

    assert opt({"A": {"X": "Hello"}, "B": "World!"}) == "Hello World!"
    assert opt({"C": "{D} {E}", "D": "foo", "E": "bar"}) == "foo bar"
    assert (
        opt(
            {
                "C": "{D} {E}",
                "D": "foo",
                "E": "bar",
                "LABREA": {"OPTIONS": {"RESOLVE": False}},
            }
        )
        == "{D} {E}"
    )


def test_validate():
    with pytest.raises(ValidationError):
        Option("A.B").validate({"A": {"X": 1}})

    with pytest.raises(ValidationError):
        Option("A").validate({"A": "{X}"})

    with pytest.raises(ValidationError):
        Option("A", "{B}").validate({})

    Option("A", "{B}").validate({"B": 1})

    Option("A").validate({"A": "{X}", "LABREA": {"OPTIONS": {"RESOLVE": False}}})


def test_docstring():
    assert Option("A").__doc__ == ""
    assert Option("A", doc="Hello, World!").__doc__ == "Hello, World!"
