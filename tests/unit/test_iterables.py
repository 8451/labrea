from labrea import dataset, Option, Map
from labrea.types import EvaluationError, ValidationError
import pytest


@dataset
def square(x: float = Option('X')) -> float:
    return x**2


@dataset
def add(x: float = Option('X'), y: float = Option('Y')) -> float:
    return x + y


@dataset
def negative(x: float = Option('NESTED.X')) -> float:
    return -x


def test_map():
    squares = Map(square).over({'X': Option('X_LIST')})
    added_nested = Map(add).over({'X': Option('X_LIST')}).over({'Y': Option('Y_LIST')})
    added_flat = Map(add).over({'X': Option('X_LIST'), 'Y': Option('Y_LIST')})
    added_over_x = Map(add).over({'X': Option('X_LIST')})
    negatives = Map(negative).over({'NESTED.X': Option('X_LIST')})

    assert squares({'X_LIST': [1, 2, 3]}) == [1, 4, 9]
    assert added_nested({'X_LIST': [1, 2], 'Y_LIST': [10, 20]}) == [[11, 12], [21, 22]]
    assert added_flat({'X_LIST': [1, 2], 'Y_LIST': [10, 20]}) == [11, 21, 12, 22]
    assert added_over_x({'X_LIST': [1, 2], 'Y': 10}) == [11, 12]
    assert negatives({'X_LIST': [1, 2, 3]}) == [-1, -2, -3]

    with pytest.raises(EvaluationError):
        squares({'X': 1})

    with pytest.raises(EvaluationError):
        added_nested({'X_LIST': [1, 2], 'Y': 10})

    with pytest.raises(EvaluationError):
        added_flat({'X_LIST': [1, 2], 'Y': 10})

    with pytest.raises(EvaluationError):
        added_over_x({'X': 1, 'Y': 10})

    with pytest.raises(EvaluationError):
        negatives({'NESTED': {'X': 1}})

    with pytest.raises(ValidationError):
        squares.validate({'X': 1})

    with pytest.raises(ValidationError):
        added_nested.validate({'X_LIST': [1, 2], 'Y': 10})

    with pytest.raises(ValidationError):
        added_flat.validate({'X_LIST': [1, 2], 'Y': 10})

    with pytest.raises(ValidationError):
        added_over_x.validate({'X': 1, 'Y': 10})

    with pytest.raises(ValidationError):
        negatives.validate({'NESTED': {'X': 1}})

    assert squares.keys({'X_LIST': [1, 2, 3]}) == {'X_LIST'}
    assert added_nested.keys({'X_LIST': [1, 2], 'Y_LIST': [10, 20]}) == {'X_LIST', 'Y_LIST'}
    assert added_flat.keys({'X_LIST': [1, 2], 'Y_LIST': [10, 20]}) == {'X_LIST', 'Y_LIST'}
    assert added_over_x.keys({'X_LIST': [1, 2], 'Y': 10}) == {'X_LIST', 'Y'}
    assert negatives.keys({'X_LIST': [1, 2, 3]}) == {'X_LIST'}
