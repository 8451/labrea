from labrea.option import Option
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


def test_is_not():
    a = Option('A') >> lf.is_not(lf.eq(1))

    assert a({'A': 0}) == True
    assert a({'A': 1}) == False
    assert a({'A': 2}) == True
