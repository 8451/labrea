from labrea.template import Template
from labrea.exceptions import KeyNotFoundError
import pytest


def test_basic():
    template = Template('{GREETING}, {:name:}!', name='World')
    options = {'GREETING': 'Hello'}

    assert template(options) == 'Hello, World!'
    template.validate(options)
    assert template.keys(options) == {'GREETING'}
    assert template.explain(options) == {'GREETING'}


def test_malformed():
    with pytest.raises(ValueError):
        Template('{GREETING} {:name:}')

    with pytest.warns(UserWarning):
        Template('{GREETING}', name='World')


def test_missing():
    template = Template('{GREETING}, {:name:}!', name='World')
    options = {}

    with pytest.raises(KeyNotFoundError) as excinfo:
        template(options)
        assert excinfo.value.key == 'GREETING'

    with pytest.raises(KeyNotFoundError) as excinfo:
        template.validate(options)
        assert excinfo.value.key == 'GREETING'

    with pytest.raises(KeyNotFoundError) as excinfo:
        template.keys(options)
        assert excinfo.value.key == 'GREETING'

    assert template.explain(options) == {'GREETING'}


def test_confectioner_templating():
    template = Template('{A} {B}{:punc:}', punc='!')
    present = {'A': '{C}', 'B': '{D}', 'C': 'Hello', 'D': 'World'}
    missing = {'A': '{C}', 'B': '{D}', 'C': 'Hello'}

    assert template(present) == 'Hello World!'
    template.validate(present)
    assert template.keys(present) == {'A', 'B', 'C', 'D'}

    with pytest.raises(KeyNotFoundError) as excinfo:
        template(missing)
        assert excinfo.value.key == 'D'

    with pytest.raises(KeyNotFoundError) as excinfo:
        template.validate(missing)
        assert excinfo.value.key == 'D'

    with pytest.raises(KeyNotFoundError) as excinfo:
        template.keys(missing)
        assert excinfo.value.key == 'D'

    assert template.explain(present) == {'A', 'B', 'C', 'D'}
    assert template.explain(missing) == {'A', 'B', 'C', 'D'}
    assert template.explain() == {'A', 'B'}


def test_repr():
    assert repr(Template('{GREETING}, {:name:}!', name='World')) == "Template('{GREETING}, {:name:}!', name=Value('World'))"
    assert repr(Template('{GREETING}')) == "Template('{GREETING}')"
