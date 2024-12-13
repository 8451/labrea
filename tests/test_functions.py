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
