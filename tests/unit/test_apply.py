from typing import Callable

from labrea import dataset, Option


def test_apply():
    X_opt = Option('X')

    @dataset
    def square_func() -> Callable[[float], float]:
        return lambda x: x ** 2

    assert (
            X_opt.apply(square_func).evaluate({'X': 2}) ==
            X_opt.apply(lambda x: x**2).evaluate({'X': 2}) ==
            4
    )
