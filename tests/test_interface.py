import pytest

from labrea.interface import interface, implements
from labrea.option import Option
from labrea.dataset import dataset
from labrea.exceptions import EvaluationError


@interface('DISPATCH')
class MyInterface:
    a: str

    def b() -> str:
        return 'b'

    @staticmethod
    @dataset
    def c() -> str:
        return 'c'

    d: str = Option('D', 'd')


@interface('DISPATCH_2')
class MyInterface2:
    e = 'e'


def test_no_implementation():
    with pytest.raises(EvaluationError):
        MyInterface.a()

    assert MyInterface.b() == 'b'
    assert MyInterface.c() == 'c'
    assert MyInterface.d() == 'd'


def test_good_implementation():
    @MyInterface.implementation('GOOD')
    class Good:
        a = 'a'

    assert MyInterface.a({'DISPATCH': 'GOOD'}) == 'a'
    assert MyInterface.b({'DISPATCH': 'GOOD'}) == 'b'
    assert MyInterface.c({'DISPATCH': 'GOOD'}) == 'c'
    assert MyInterface.d({'DISPATCH': 'GOOD'}) == 'd'


def test_bad_implementation():
    with pytest.raises(TypeError):
        @MyInterface.implementation('BAD')
        class Bad:
            pass

    with pytest.raises(TypeError):
        @MyInterface.implementation('BAD')
        class Bad:
            a = 'a'
            f = 'f'


def test_override():
    @MyInterface.implementation('OVERRIDE')
    class Good:
        a = 'A'

        def b():
            return 'B'

        @staticmethod
        @dataset
        def c():
            return 'C'

        d = Option('D', 'D')

    assert MyInterface.a({'DISPATCH': 'OVERRIDE'}) == 'A'
    assert MyInterface.b({'DISPATCH': 'OVERRIDE'}) == 'B'
    assert MyInterface.c({'DISPATCH': 'OVERRIDE'}) == 'C'
    assert MyInterface.d({'DISPATCH': 'OVERRIDE'}) == 'D'


def test_multi_implementation():
    @implements(MyInterface, MyInterface2, alias='MULTI')
    class Multi:
        a = 'a'

    assert MyInterface.a({'DISPATCH': 'MULTI'}) == 'a'
    assert MyInterface.b({'DISPATCH': 'MULTI'}) == 'b'
    assert MyInterface.c({'DISPATCH': 'MULTI'}) == 'c'
    assert MyInterface.d({'DISPATCH': 'MULTI'}) == 'd'
    assert MyInterface2.e({'DISPATCH_2': 'MULTI'}) == 'e'


def test_missing_args():
    with pytest.raises(TypeError):
        @interface
        class A:
            pass

    with pytest.raises(TypeError):
        @MyInterface.implementation
        class A:
            pass


def test_invalid_member():
    with pytest.raises(AttributeError):
        @interface('A')
        class A:
            implementation = 'implementation'


def test_repr():
    @MyInterface.implementation('A')
    class A:
        a: int = 1

    assert repr(MyInterface) == '<Interface test_interface.MyInterface>'
    assert repr(A) == '<Implementation test_interface.A of MyInterface>'
