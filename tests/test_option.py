from labrea.exceptions import KeyNotFoundError
from labrea.option import AllOptions, Option, WithOptions, WithDefaultOptions
from labrea.template import Template
from labrea.types import Value
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


def test_with_default_options():
    w = WithDefaultOptions(Option('A'), {'A': 42})

    assert w.evaluate({}) == 42
    assert w.evaluate({'A': 43}) == 43

    w.validate({})
    w.validate({'A': 43})

    assert w.keys({}) == set()
    assert w.keys({'A': 43}) == {'A'}

    assert w.explain({}) == set()
    assert w.explain({'A': 43}) == {'A'}

    assert repr(w) == "WithDefaultOptions(Option('A'), {'A': 42})"


def test_all_options():
    options = {'A': 'X', 'B': 'Y', 'C': '{A}/{B}'}
    resolved = {'A': 'X', 'B': 'Y', 'C': 'X/Y'}

    assert AllOptions.evaluate(options) == resolved
    AllOptions.validate(options)
    assert AllOptions.keys(options) == {'A', 'B', 'C'}
    assert AllOptions.explain(options) == {'A', 'B', 'C'}
    assert AllOptions.explain() == set()
    assert repr(AllOptions) == "AllOptions"


def test_all_options_cannot_resolve():
    options = {"A": "{B}"}
    with pytest.raises(KeyNotFoundError) as excinfo:
        AllOptions.evaluate(options)
        assert excinfo.value.key == 'B'
    with pytest.raises(KeyNotFoundError) as excinfo:
        AllOptions.validate(options)
        assert excinfo.value.key == 'B'


def test_namespace_full():
    @Option.namespace("PKG")
    class PKG:
        A: str

    inner = {"A": "a"}
    options = {"PKG": inner}

    assert PKG(options) == inner
    PKG.validate(options)
    assert PKG.keys(options) == {"PKG"}
    assert PKG.explain(options) == {"PKG"}
    assert PKG.explain() == set()

    assert repr(PKG) == "Namespace('PKG')"


def test_namespace_inferred():
    @Option.namespace
    class PKG:
        A: str
        class MODULE:
            B: int

    assert PKG.A({"PKG": {"A": "a"}}) == "a"
    assert PKG.MODULE.B({"PKG": {"MODULE": {"B": 1}}}) == 1


def test_namespace_explicit():
    @Option.namespace("MY-PKG")
    class PKG:
        A = Option("X")
        @Option.namespace("MY-MODULE")
        class MODULE:
            B = Option("Y")

    assert PKG.A({"MY-PKG": {"X": "a"}}) == "a"
    assert PKG.MODULE.B({"MY-PKG": {"MY-MODULE": {"Y": 1}}}) == 1


def test_namespace_auto():
    @Option.namespace
    class PKG:
        A = Option.auto(doc="A as string") >> str
        B = Option.auto(doc="B")

    assert PKG.A({"PKG": {"A": 1}}) == "1"
    assert PKG.A.__doc__ == "A as string"
    assert PKG.B.__doc__ == "B"


def test_namespace_default():
    @Option.namespace
    class PKG:
        A: str = "a"
        B = Value(1) >> str

    assert PKG.A() == "a"
    assert PKG.B() == "1"

    with pytest.raises(TypeError):
        @Option.namespace
        class _:
            A = object()



def test_namespace_doc():
    @Option.namespace
    class PKG:
        A: str
        class MODULE:
            B = Option.auto(1, doc="B")

    assert PKG.__doc__ == 'Namespace PKG:\n  Option PKG.A\n  Namespace PKG.MODULE:\n    Option PKG.MODULE.B (default 1): B'
