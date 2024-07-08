import pytest

from labrea.types import Evaluatable, Value
from labrea.exceptions import EvaluationError, KeyNotFoundError
from labrea.option import Option


def test_value():
    value = Value(42)
    assert value.evaluate({}) == value() == 42
    assert value.validate({}) is None
    assert value.keys({}) == set()
    assert value.explain() == value.explain({}) == set()
    assert repr(value) == "Value(42)"
    assert value == value
    assert value != Value(43)

    class Uncopyable:
        def __deepcopy__(self, memo):
            raise NotImplementedError('Cannot copy this.')

    uncopyable = Uncopyable()

    assert Value(uncopyable).evaluate({}) is uncopyable


def test_unit():
    assert Evaluatable.unit(1)() == 1


@pytest.mark.parametrize(
    'wrapper,method',
    [
        (wrapper, method)
        for wrapper in (Value, lambda x: x)
        for method in ('apply', 'rshift')
    ]
)
def test_apply(wrapper, method):
    value = Value(42)

    def incr(x):
        return x + 1

    if method == 'apply':
        apply = value.apply(wrapper(incr))
    else:
        apply = value >> wrapper(incr)

    assert apply.evaluate({}) == 43
    assert apply.validate({}) is None
    assert apply.keys({}) == set()
    assert apply.explain() == set()
    assert repr(apply) == f"Value(42).apply(Value({repr(incr)}))"


def test_bind():
    value = Value(42)

    def incr(x):
        return Value(x + 1)

    bind = value.bind(incr)
    assert bind.evaluate({}) == 43
    assert bind.validate({}) is None
    assert bind.keys({}) == set()
    assert bind.explain() == set()
    assert repr(bind) == f"Value(42).bind({repr(incr)})"


def test_type_error():
    with pytest.raises(TypeError):
        Value(42).bind(42)

    with pytest.raises(TypeError):
        Value(42).apply(42)


def test_error_str():
    assert str(EvaluationError('message', Value(1))) == "Originating in Value(1) | message"
    assert str(KeyNotFoundError('key', Value(1))) == "Originating in Value(1) | Key 'key' not found"


def test_fingerprint():
    value = Value(42)
    option = Option('A')

    assert value.fingerprint({}) == value.fingerprint({'A': 1})
    assert value.fingerprint({'A': 1}) != option.fingerprint({'A': 1})
    assert option.fingerprint({'A': 1}) == option.fingerprint({'A': 1})
    assert option.fingerprint({'A': 1}) != option.fingerprint({'A': 2})
    assert option.fingerprint({'A': 1}) == option.fingerprint({'A': 1, 'V': 2})


def test_result():
    option = Option('A')
    assert option.result is option
