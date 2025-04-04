from labrea.option import Option
from labrea.types import Value
import labrea.functions as lf


def test_partial():
    p = Option('A') >> lf.partial(lambda x, y: x + y, 1)

    assert p({'A': 2}) == 3


def test_map():
    m = Option('A') >> lf.map(str) >> list

    assert m({'A': [1, 2]}) == ['1', '2']


def test_filter():
    f = Option('A') >> lf.filter(lambda x: x % 2 == 0) >> list

    assert f({'A': [1, 2, 3, 4]}) == [2, 4]


def test_reduce():
    r1 = Option('A') >> lf.reduce(lambda x, y: x + y)
    r2 = Option('A') >> lf.reduce(lambda x, y: x + y, 10)

    assert r1({'A': [1, 2, 3, 4]}) == 10
    assert r2({'A': [1, 2, 3, 4]}) == 20


def test_into():
    i = Option('A') >> lf.into(lf.partial(lambda x, y, z: x + y + z, z=3))

    assert i({'A': [1, 2]}) == 6
    assert i({'A': {'x': 1, 'y': 2}}) == 6


def test_flatmap():
    f = Option('A') >> lf.flatmap(lambda x: [x, x]) >> list

    assert f({'A': [1, 2]}) == [1, 1, 2, 2]


def test_map_items():
    f = Option('A') >> dict >> lf.map_items(lambda k, v: (k + 1, v + 1)) >> dict

    assert f({'A': [[1, 1], [2, 2]]}) == {2: 2, 3: 3}


def test_map_keys():
    f = Option('A') >> dict >> lf.map_keys(lambda k: k + 1) >> dict

    assert f({'A': [[1, 1], [2, 2]]}) == {2: 1, 3: 2}


def test_map_values():
    f = Option('A') >> dict >> lf.map_values(lambda v: v + 1) >> dict

    assert f({'A': [[1, 1], [2, 2]]}) == {1: 2, 2: 3}


def test_filter_items():
    f = Option('A') >> dict >> lf.filter_items(lambda k, v: (k * v) % 2 == 0) >> dict

    assert f({'A': [[1, 1], [2, 2], [3, 3], [4, 4]]}) == {2: 2, 4: 4}


def test_filter_keys():
    f = Option('A') >> dict >> lf.filter_keys(lambda k: k % 2 == 0) >> dict

    assert f({'A': [[1, 1], [2, 2], [3, 3], [4, 4]]}) == {2: 2, 4: 4}


def test_filter_values():
    f = Option('A') >> dict >> lf.filter_values(lambda v: v % 2 == 0) >> dict

    assert f({'A': [[1, 1], [2, 2], [3, 3], [4, 4]]}) == {2: 2, 4: 4}


def test_concat():
    a = Option('A') >> lf.concat([1]) >> list

    assert a({'A': [0]}) == [0, 1]


def append():
    a = Option('A') >> lf.append(1) >> list

    assert a({'A': [0]}) == [0, 1]


def test_intersect():
    a = Option('A') >> lf.intersect([1, 2])

    assert a({'A': [0, 1]}) == {1}


def test_union():
    a = Option('A') >> lf.union([1, 2])

    assert a({'A': [0, 1]}) == {0, 1, 2}


def test_difference():
    a = Option('A') >> lf.difference([1, 2])

    assert a({'A': [0, 1]}) == {0}


def test_symmetric_difference():
    a = Option('A') >> lf.symmetric_difference([1, 2])

    assert a({'A': [0, 1]}) == {0, 2}


def test_get():
    a = Option('A') >> lf.get('B')
    b = Option('A') >> lf.get('B', None)
    c = Option('A') >> lf.get(1)
    d = Option('A') >> lf.get(1, default=100)

    assert a({'A': {'B': 'b'}}) == 'b'
    assert b({'A': {'B': 'b'}}) == 'b'
    assert b({'A': {'C': 'c'}}) is None
    assert c({'A': [1, 2]}) == 2
    assert d({'A': [1, 2]}) == 2
    assert d({'A': [1]}) == 100


def test_add():
    a = Option('A') >> lf.add(1)

    assert a({'A': 1}) == 2


def test_subtract():
    a = Option('A') >> lf.subtract(1)

    assert a({'A': 1}) == 0


def test_multiply():
    a = Option('A') >> lf.multiply(2)

    assert a({'A': 2}) == 4


def test_divide():
    a = Option('A') >> lf.divide_by(2)

    assert a({'A': 4}) == 2


def test_left_multiply():
    a = Option('A') >> lf.left_multiply(2)

    assert a({'A': 2}) == 4


def test_divide_into():
    a = Option('A') >> lf.divide_into(2)

    assert a({'A': 4}) == 0.5


def test_negate():
    a = Option('A') >> lf.negate

    assert a({'A': 1}) == -1
    assert a({'A': -1}) == 1


def test_merge():
    a = Option('A') >> lf.merge({'B': 2})

    assert a({'A': {'A': 0, 'B': 1}}) == {'A': 0, 'B': 2}



def test_length():
    a = Option('A') >> lf.length

    assert a({'A': [0, 1]}) == 2


def test_eq():
    e = Option('A') >> lf.eq(1)

    assert e({'A': 1}) == True
    assert e({'A': 2}) == False


def test_ne():
    e = Option('A') >> lf.ne(1)

    assert e({'A': 1}) == False
    assert e({'A': 2}) == True


def test_lt():
    e = Option('A') >> lf.lt(1)

    assert e({'A': 0}) == True
    assert e({'A': 1}) == False
    assert e({'A': 2}) == False


def test_le():
    e = Option('A') >> lf.le(1)

    assert e({'A': 0}) == True
    assert e({'A': 1}) == True
    assert e({'A': 2}) == False


def test_gt():
    e = Option('A') >> lf.gt(1)

    assert e({'A': 0}) == False
    assert e({'A': 1}) == False
    assert e({'A': 2}) == True


def test_ge():
    e = Option('A') >> lf.ge(1)

    assert e({'A': 0}) == False
    assert e({'A': 1}) == True
    assert e({'A': 2}) == True


def test_positive():
    a = Option('A') >> lf.positive

    assert a({'A': -1}) == False
    assert a({'A': 0}) == False
    assert a({'A': 1}) == True


def test_negative():
    a = Option('A') >> lf.negative

    assert a({'A': -1}) == True
    assert a({'A': 0}) == False
    assert a({'A': 1}) == False


def test_non_positive():
    a = Option('A') >> lf.non_positive

    assert a({'A': -1}) == True
    assert a({'A': 0}) == True
    assert a({'A': 1}) == False


def test_non_negative():
    a = Option('A') >> lf.non_negative

    assert a({'A': -1}) == False
    assert a({'A': 0}) == True
    assert a({'A': 1}) == True


def test_even():
    a = Option('A') >> lf.even

    assert a({'A': 0}) == True
    assert a({'A': 1}) == False


def test_odd():
    a = Option('A') >> lf.odd

    assert a({'A': 0}) == False
    assert a({'A': 1}) == True


def test_is_none():
    a = Option('A') >> lf.is_none

    assert a({'A': None}) == True
    assert a({'A': 0}) == False


def test_is_not_none():
    a = Option('A') >> lf.is_not_none

    assert a({'A': None}) == False
    assert a({'A': 0}) == True


def test_instance_of():
    e = Option('A') >> lf.instance_of(int)

    assert e({'A': 1}) == True
    assert e({'A': '1'}) == False


def test_all():
    a = Option('A') >> lf.all(lf.gt(1), lf.lt(2))

    assert a({'A': 1}) == False
    assert a({'A': 1.5}) == True
    assert a({'A': 2}) == False


def test_any():
    a = Option('A') >> lf.any(lf.le(1), lf.ge(2))

    assert a({'A': 1}) == True
    assert a({'A': 1.5}) == False
    assert a({'A': 2}) == True


def test_invert():
    a = Option('A') >> lf.invert(lf.eq(1))

    assert a({'A': 0}) == True
    assert a({'A': 1}) == False
    assert a({'A': 2}) == True

    b = Option('B') >> lf.invert()

    assert b({'B': True}) == False
    assert b({'B': False}) == True


def test_is_in():
    a = Option('A') >> lf.is_in([1, 2])

    assert a({'A': 0}) == False
    assert a({'A': 1}) == True
    assert a({'A': 2}) == True
    assert a({'A': 3}) == False


def test_is_not_in():
    a = Option('A') >> lf.is_not_in([1, 2])

    assert a({'A': 0}) == True
    assert a({'A': 1}) == False
    assert a({'A': 2}) == False
    assert a({'A': 3}) == True


def test_one_of():
    a = Option('A') >> lf.one_of(1, 2)

    assert a({'A': 0}) == False
    assert a({'A': 1}) == True
    assert a({'A': 2}) == True
    assert a({'A': 3}) == False


def test_none_of():
    a = Option('A') >> lf.none_of(1, 2)

    assert a({'A': 0}) == True
    assert a({'A': 1}) == False
    assert a({'A': 2}) == False
    assert a({'A': 3}) == True


def test_contains():
    a = Option('A') >> lf.contains(1)

    assert a({'A': [1, 2, 3]}) == True
    assert a({'A': [2, 3]}) == False


def test_does_not_contain():
    a = Option('A') >> lf.does_not_contain(1)

    assert a({'A': [1, 2, 3]}) == False
    assert a({'A': [2, 3]}) == True


def test_get_attribute():
    class Test:
        def __init__(self, value):
            self.value = value

    a = Value(Test(1)) >> lf.get_attribute('value')

    assert a() == 1


def test_call_method():
    class Test:
        def __init__(self, value):
            self.value = value

        def method(self, x):
            return self.value + x

    a = Value(Test(1)) >> lf.call_method('method', 2)

    assert a() == 3
