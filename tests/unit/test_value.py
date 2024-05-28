from labrea.types import Value


def test_uncopyable():
    class Uncopyable:
        def __deepcopy__(self, memo):
            raise NotImplementedError("Cannot copy this.")

    uncopyable = Uncopyable()

    assert Value(uncopyable).evaluate({}) is uncopyable
