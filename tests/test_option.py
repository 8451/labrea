from labrea.exceptions import KeyNotFoundError
from labrea.option import Option, WithOptions
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
    options = {'A': 42, 'V': 43}

    assert option.evaluate(options) == 42
    option.validate(options)
    assert option.keys(options) == {'A'}
    assert option.explain(options) == {'A'}


def test_missing():
    option = Option('A')
    options = {'V': 42}

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


def test_default_factory():
    option = Option('A', default_factory=lambda: 42)
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
    option = Option('A', default=Option('V'))
    options = {'V': 42}

    assert option.evaluate(options) == 42
    option.validate(options)
    assert option.keys(options) == {'V'}
    assert option.explain(options) == {'V'}
    assert option.explain() == {'V'}


def test_nested():
    option = Option('A.V')
    options = {'A': {'V': 42}}

    assert option.evaluate(options) == 42
    option.validate(options)
    assert option.keys(options) == {'A.V'}
    assert option.explain(options) == {'A.V'}


def test_nested_missing():
    option = Option('A.V')
    options = {'A': {}}

    with pytest.raises(KeyNotFoundError) as excinfo:
        option.evaluate(options)
        assert excinfo.value.key == 'A.V'

    with pytest.raises(KeyNotFoundError) as excinfo:
        option.validate(options)
        assert excinfo.value.key == 'A.V'

    with pytest.raises(KeyNotFoundError) as excinfo:
        option.keys(options)
        assert excinfo.value.key == 'A.V'

    assert option.explain(options) == {'A.V'}


def test_template_default():
    option = Option('A', default='{V}.{C}')
    assert isinstance(option.default, Template)


def test_confectioner_templating():
    option = Option('A')
    present = {'A': '{V} {C}!', 'V': 'Hello', 'C': 'World'}
    missing = {'A': '{V} {C}!', 'V': 'Hello'}

    assert option.evaluate(present) == 'Hello World!'
    option.validate(present)
    assert option.keys(present) == {'A', 'V', 'C'}

    with pytest.raises(KeyNotFoundError) as excinfo:
        option.evaluate(missing)
        assert excinfo.value.key == 'C'

    with pytest.raises(KeyNotFoundError) as excinfo:
        option.validate(missing)
        assert excinfo.value.key == 'C'

    with pytest.raises(KeyNotFoundError) as excinfo:
        option.keys(missing)
        assert excinfo.value.key == 'C'

    assert option.explain(present) == {'A', 'V', 'C'}
    assert option.explain(missing) == {'A', 'V', 'C'}
    assert option.explain() == {'A'}


def test_repr():
    assert repr(Option('A')) == "Option('A')"
    assert repr(Option('A', default=42)) == "Option('A', default=Value(42))"
    assert repr(Option('A', default='{V}.{C}')) == f"Option('A', default={repr(Template('{V}.{C}'))})"
    assert repr(Option('A', doc='Hello, World!')) == "Option('A')"


def test_with_options():
    w = WithOptions(Option('A'), {'A': 42})

    assert w.evaluate({}) == 42
    assert w.evaluate({'A': 43}) == 42

    w.validate({})
    w.validate({'A': 43})

    assert w.keys({}) == set()
    assert w.keys({'A': 43}) == set()

    assert w.explain({}) == set()
    assert w.explain({'A': 43}) == set()

    assert repr(w) == "WithOptions(Option('A'), {'A': 42})"
