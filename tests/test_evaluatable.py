import pytest

from labrea.evaluatable import Evaluatable, Value, KeyNotFoundError


def test_value():
    value = Value(42)
    assert value.evaluate({}) == value() == 42
    assert value.validate({}) is None
    assert value.keys({}) == set()
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


@pytest.mark.parametrize('wrapper', [Value, lambda x: x])
def test_apply(wrapper):
    value = Value(42)

    def incr(x):
        return x + 1

    apply = value.apply(wrapper(incr))
    assert apply.evaluate({}) == 43
    assert apply.validate({}) is None
    assert apply.keys({}) == set()
    assert repr(apply) == f"Value(42).apply(Value({repr(incr)}))"


def test_bind():
    value = Value(42)

    def incr(x):
        return Value(x + 1)

    bind = value.bind(incr)
    assert bind.evaluate({}) == 43
    assert bind.validate({}) is None
    assert bind.keys({}) == set()
    assert repr(bind) == f"Value(42).bind({repr(incr)})"


def test_panic():
    with pytest.raises(KeyNotFoundError) as excinfo:
        Value(42).panic("key")
        assert excinfo.value.key == "key"
        assert excinfo.value.evaluatable == Value(42)
        assert excinfo.value.source is None

    with pytest.raises(KeyNotFoundError) as excinfo:
        source = Exception()
        Value(42).panic("key", source)
        assert excinfo.value.key == "key"
        assert excinfo.value.evaluatable == Value(42)
        assert excinfo.value.source is source



