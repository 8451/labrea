import labrea.mock
from labrea import Option


def test_mock():
    A = Option("A")

    with labrea.mock.Mock() as mock:
        mock(A, 1)
        assert A() == 1
        A.validate({})
        assert A.keys({}) == set()
        assert A.explain() == set()

        mock(A, Option("B"))
        assert A({"B": 2}) == 2
        A.validate({"B": 2})
        assert A.keys({"B": 2}) == {"B"}
        assert A.explain() == {"B"}

    assert A({"A": 1}) == 1
    A.validate({"A": 1})
    assert A.keys({"A": 1}) == {"A"}
    assert A.explain() == {"A"}
