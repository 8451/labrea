import pytest

from labrea.interface import interface, implements
from labrea.option import Option
from labrea.dataset import dataset, abstractdataset
from labrea.exceptions import EvaluationError


@interface('DISPATCH')
class MyInterface:
    a: str

    @staticmethod
    @abstractdataset
    def b() -> str:
        pass

    def c() -> str:
        return 'c'

    @staticmethod
    @dataset
    def d() -> str:
        return 'd'

    e: str = Option('E', 'e')


@interface('DISPATCH_2')
class MyInterface2:
    f = 'f'


def test_no_implementation():
    with pytest.raises(EvaluationError):
        MyInterface.a()

    with pytest.raises(EvaluationError):
        MyInterface.b()

    assert MyInterface.c() == 'c'
    assert MyInterface.d() == 'd'
    assert MyInterface.e() == 'e'


def test_good_implementation():
    @MyInterface.implementation('GOOD')
    class Good:
        a = 'a'
        b = 'b'

    assert MyInterface.a({'DISPATCH': 'GOOD'}) == 'a'
    assert MyInterface.b({'DISPATCH': 'GOOD'}) == 'b'
    assert MyInterface.c({'DISPATCH': 'GOOD'}) == 'c'
    assert MyInterface.d({'DISPATCH': 'GOOD'}) == 'd'
    assert MyInterface.e({'DISPATCH': 'GOOD'}) == 'e'


def test_bad_implementation():
    with pytest.raises(TypeError):
        @MyInterface.implementation('BAD')
        class Bad:
            pass

    with pytest.raises(TypeError):
        @MyInterface.implementation('BAD')
        class Bad:
            a = 'a'

    with pytest.raises(TypeError):
        @MyInterface.implementation('BAD')
        class Bad:
            b = 'b'

    with pytest.raises(TypeError):
        @MyInterface.implementation('BAD')
        class Bad:
            a = 'a'
            b = 'b'
            f = 'f'


def test_override():
    @MyInterface.implementation('OVERRIDE')
    class Good:
        a = 'A'
        b = 'B'

        def c():
            return 'C'

        @staticmethod
        @dataset
        def d():
            return 'D'

        e = Option('E', 'E')

    assert MyInterface.a({'DISPATCH': 'OVERRIDE'}) == 'A'
    assert MyInterface.b({'DISPATCH': 'OVERRIDE'}) == 'B'
    assert MyInterface.c({'DISPATCH': 'OVERRIDE'}) == 'C'
    assert MyInterface.d({'DISPATCH': 'OVERRIDE'}) == 'D'
    assert MyInterface.e({'DISPATCH': 'OVERRIDE'}) == 'E'


def test_multi_implementation():
    @implements(MyInterface, MyInterface2, alias='MULTI')
    class Multi:
        a = 'a'
        b = 'b'

    assert MyInterface.a({'DISPATCH': 'MULTI'}) == 'a'
    assert MyInterface.b({'DISPATCH': 'MULTI'}) == 'b'
    assert MyInterface.c({'DISPATCH': 'MULTI'}) == 'c'
    assert MyInterface.d({'DISPATCH': 'MULTI'}) == 'd'
    assert MyInterface.e({'DISPATCH_2': 'MULTI'}) == 'e'
    assert MyInterface2.f({'DISPATCH_2': 'MULTI'}) == 'f'


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
        a: str = 'a'
        b: str = 'b'

    assert repr(MyInterface) == '<Interface test_interface.MyInterface>'
    assert repr(A) == '<Implementation test_interface.A of MyInterface>'
