import builtins
import functools
from typing import Callable, Iterable, TypeVar

from ._missing import MISSING, MaybeMissing

A = TypeVar("A")
B = TypeVar("B")


def map(func: Callable[[A], B]) -> Callable[[Iterable[A]], Iterable[B]]:
    return functools.partial(builtins.map, func)  # type: ignore


def filter(func: Callable[[A], bool]) -> Callable[[Iterable[A]], Iterable[A]]:
    return functools.partial(builtins.filter, func)  # type: ignore


def reduce(
    func: Callable[[A, A], A], initial: MaybeMissing[A] = MISSING
) -> Callable[[Iterable[A]], A]:
    if initial is MISSING:
        return functools.partial(functools.reduce, func)

    return lambda iterable: functools.reduce(func, iterable, initial)  # type: ignore
