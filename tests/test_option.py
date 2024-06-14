from labrea.evaluatable import KeyNotFoundError
from labrea.option import Option
from labrea.template import Template
import pytest


def test_basic():
    option = Option('A')
    options = {'A': 42}

    assert option.evaluate(options) == 42
    option.validate(options)
    assert option.keys(options) == {'A'}
    assert option.explain(options) == {'A'}
    assert option.explain() == {'A'}


def test_multiple_provided():
    option = Option('A')
    options = {'A': 42, 'B': 43}

    assert option.evaluate(options) == 42
    option.validate(options)
    assert option.keys(options) == {'A'}
    assert option.explain(options) == {'A'}


def test_missing():
    option = Option('A')
    options = {'B': 42}

    with pytest.raises(KeyNotFoundError) as excinfo:
        option.evaluate(options)
        assert excinfo.value.key == 'A'

    with pytest.raises(KeyNotFoundError) as excinfo:
        option.validate(options)
        assert excinfo.value.key == 'A'

    with pytest.raises(KeyNotFoundError) as excinfo:
        option.keys(options)
        assert excinfo.value.key == 'A'

    assert option.explain(options) == {'A'}


def test_default():
    option = Option('A', default=42)
    missing = {}
    provided = {'A': 43}

    assert option.evaluate(missing) == 42
    option.validate(missing)
    assert option.keys(missing) == set()
    assert option.explain(missing) == set()

    assert option.evaluate(provided) == 43
    option.validate(provided)
    assert option.keys(provided) == {'A'}
    assert option.explain(provided) == {'A'}


def test_evaluatable_default():
    option = Option('A', default=Option('B'))
    options = {'B': 42}

    assert option.evaluate(options) == 42
    option.validate(options)
    assert option.keys(options) == {'B'}
    assert option.explain(options) == {'B'}
    assert option.explain() == {'B'}


def test_nested():
    option = Option('A.B')
    options = {'A': {'B': 42}}

    assert option.evaluate(options) == 42
    option.validate(options)
    assert option.keys(options) == {'A.B'}
    assert option.explain(options) == {'A.B'}


def test_nested_missing():
    option = Option('A.B')
    options = {'A': {}}

    with pytest.raises(KeyNotFoundError) as excinfo:
        option.evaluate(options)
        assert excinfo.value.key == 'A.B'

    with pytest.raises(KeyNotFoundError) as excinfo:
        option.validate(options)
        assert excinfo.value.key == 'A.B'

    with pytest.raises(KeyNotFoundError) as excinfo:
        option.keys(options)
        assert excinfo.value.key == 'A.B'

    assert option.explain(options) == {'A.B'}


def test_template_default():
    option = Option('A', default='{B}.{C}')
    assert isinstance(option.default, Template)


def test_confectioner_templating():
    option = Option('A')
    present = {'A': '{B} {C}!', 'B': 'Hello', 'C': 'World'}
    missing = {'A': '{B} {C}!', 'B': 'Hello'}

    assert option.evaluate(present) == 'Hello World!'
    option.validate(present)
    assert option.keys(present) == {'A', 'B', 'C'}

    with pytest.raises(KeyNotFoundError) as excinfo:
        option.evaluate(missing)
        assert excinfo.value.key == 'C'

    with pytest.raises(KeyNotFoundError) as excinfo:
        option.validate(missing)
        assert excinfo.value.key == 'C'

    with pytest.raises(KeyNotFoundError) as excinfo:
        option.keys(missing)
        assert excinfo.value.key == 'C'

    assert option.explain(present) == {'A', 'B', 'C'}
    assert option.explain(missing) == {'A', 'B', 'C'}
    assert option.explain() == {'A'}


def test_repr():
    assert repr(Option('A')) == "Option('A')"
    assert repr(Option('A', default=42)) == "Option('A', default=Value(42))"
    assert repr(Option('A', default='{B}.{C}')) == f"Option('A', default={repr(Template('{B}.{C}'))})"
    assert repr(Option('A', doc='Hello, World!')) == "Option('A')"
