import pytest

import tests.ext.interfaces
import tests.pkg.interfaces
from labrea import Interface, Option, interface
from labrea.types import EvaluationError


def test_base():
    config = {"B": "B"}

    with pytest.raises(EvaluationError):
        _ = tests.pkg.interfaces.Interface1.a(config)

    assert tests.pkg.interfaces.Interface1.b.evaluate(config) == "B"
    assert tests.pkg.interfaces.Interface1.c.evaluate(config) == "default"


def test_imp():
    config = {
        "B": "B",
        "LABREA": {
            "IMPLEMENTATIONS": {
                "tests": {
                    "pkg": {
                        "interfaces": {"Interface1": "tests.ext.interfaces.Int1Imp"}
                    }
                }
            },
            "REQUIRES": ["tests.ext"],
        },
    }

    assert tests.pkg.interfaces.Interface1.a.evaluate(config) == 1
    assert tests.pkg.interfaces.Interface1.b.evaluate(config) == "B"
    assert tests.pkg.interfaces.Interface1.c.evaluate(config) == "overload"


def test_multi():
    config = {"A": "A", "B": "B", "LABREA": {"IMPLEMENTATIONS": {"A": "X", "B": "XX"}}}

    @interface.dispatch("LABREA.IMPLEMENTATIONS.A")
    class A:
        a: int

    @interface.dispatch("LABREA.IMPLEMENTATIONS.B")
    class B:
        b: int

    with pytest.raises(TypeError):

        @Interface.implementation(A, B)
        class W:
            a = Option("A")

    @Interface.implementation(A, B, aliases=["X", "XX"])
    class X:
        a = Option("A")
        b = Option("B")

    assert A.a(config) == "A"
    assert B.b(config) == "B"


def test_other_evaluatable():
    @interface(dispatch="INT")
    class Int:
        a: int = Option("A")
        b: int = 2

    @Int.implementation(alias="Imp")
    class Imp:
        a: int = 3

    assert Int.a({"A": 1}) == 1
    assert Int.b({}) == 2
    assert Int.a({"INT": "Imp"}) == 3


def test_no_interfaces():
    with pytest.raises(TypeError):

        @Interface.implementation()
        class X:
            pass
