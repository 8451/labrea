import pytest

from labrea import Field, datasetclass


def test_bad_annotation():
    with pytest.raises(AttributeError):

        @datasetclass
        class Bad:
            x: int


def test_auto_field():
    @datasetclass
    class AutoField:
        x: int = 1

    assert AutoField.x == Field(1)
