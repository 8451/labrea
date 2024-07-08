import builtins
import functools
from typing import Callable, Iterable, TypeVar

from ._missing import MISSING, MaybeMissing
from .application import FunctionApplication
from .pipeline import PipelineStep
from .types import MaybeEvaluatable

A = TypeVar("A")
B = TypeVar("B")


def map(
    func: MaybeEvaluatable[Callable[[A], B]]
) -> PipelineStep[Iterable[A], Iterable[B]]:
    return PipelineStep(
        FunctionApplication(
            functools.partial, builtins.map, func  # type: ignore [arg-type]
        ),
        f"map({func!r})",
    )


def filter(
    func: MaybeEvaluatable[Callable[[A], bool]]
) -> PipelineStep[Iterable[A], Iterable[A]]:
    return PipelineStep(
        FunctionApplication(
            functools.partial, builtins.filter, func  # type: ignore [arg-type]
        ),
        f"filter({func!r})",
    )


def _reduce(
    func: Callable[[A, A], A], iterable: Iterable[A], initial: MaybeMissing[A]
) -> A:
    if initial is MISSING:
        return functools.reduce(func, iterable)

    return functools.reduce(func, iterable, initial)


def reduce(
    func: MaybeEvaluatable[Callable[[A, A], A]],
    initial: MaybeMissing[MaybeEvaluatable[A]] = MISSING,
) -> PipelineStep[Iterable[A], A]:
    return PipelineStep(
        FunctionApplication(
            functools.partial, _reduce, func, initial=initial  # type: ignore [arg-type]
        ),
        f"reduce({func!r})"
        if initial is MISSING
        else f"reduce({func!r}, initial={initial!r})",
    )
