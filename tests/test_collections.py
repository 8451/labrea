from labrea.collections import (
    evaluatable_dict,
    evaluatable_list,
    evaluatable_set,
    evaluatable_tuple,
)
from labrea.option import Option


def test_dict():
    assert evaluatable_dict({'a': Option('A'), 'b': 2}).evaluate({'A': 1}) == {'a': 1, 'b': 2}


def test_list():
    assert evaluatable_list(Option('A'), 2).evaluate({'A': 1}) == [1, 2]


def test_set():
    assert evaluatable_set(Option('A'), 2).evaluate({'A': 1}) == {1, 2}


def test_tuple():
    assert evaluatable_tuple(Option('A'), 2).evaluate({'A': 1}) == (1, 2)