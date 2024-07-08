from labrea.option import Option
import labrea.functions as lf


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
