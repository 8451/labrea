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
    """Create a pipeline step that maps a function over an iterable.

    This allows for calling map in a functional style over an iterable
    using the :code:`.apply()` method or the :code:`>>` operator on an
    Evaluatable object that returns an iterable.

    Arguments
    ----------
    func : MaybeEvaluatable[Callable[[A], B]]
        The function to apply to each element of the iterable. This can be
        an Evaluatable that returns a function, or a constant function.


    Example Usage
    -------------
    >>> from labrea import Option
    >>> import labrea.functions as F
    >>>
    >>> (Option('A') >> F.map(lambda x: x + 1))({'A': [1, 2, 3, 4]})
    [2, 3, 4, 5]
    """
    return PipelineStep(
        FunctionApplication(
            functools.partial, builtins.map, func  # type: ignore [arg-type]
        ),
        f"map({func!r})",
    )


def filter(
    func: MaybeEvaluatable[Callable[[A], bool]]
) -> PipelineStep[Iterable[A], Iterable[A]]:
    """Create a pipeline step that filters an iterable using a predicate function.

    This allows for calling filter in a functional style over an iterable
    using the :code:`.apply()` method or the :code:`>>` operator on an
    Evaluatable object that returns an iterable.

    Arguments
    ----------
    func : MaybeEvaluatable[Callable[[A], bool]]
        The predicate function to apply to each element of the iterable. This
        can be an Evaluatable that returns a function, or a constant function.


    Example Usage
    -------------
    >>> from labrea import Option
    >>> import labrea.functions as F
    >>>
    >>> (Option('A') >> F.filter(lambda x: x % 2 == 0))({'A': [1, 2, 3, 4]})
    [2, 4]
    """
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
    """Create a pipeline step that reduces an iterable using a binary function.

    This allows for calling reduce in a functional style over an iterable
    using the :code:`.apply()` method or the :code:`>>` operator on an
    Evaluatable object that returns an iterable.

    Arguments
    ----------
    func : MaybeEvaluatable[Callable[[A, A], A]]
        The binary function to apply to each element of the iterable. This
        can be an Evaluatable that returns a function, or a constant function.
    initial : MaybeMissing[MaybeEvaluatable[A]], optional
        The initial value to use for the reduction. If not provided, the
        first element of the iterable is used as the initial value. This
        can be an Evaluatable that returns a value, or a constant value.


    Example Usage
    -------------
    >>> from labrea import Option
    >>> import labrea.functions as F
    >>>
    >>> (Option('A') >> F.reduce(lambda x, y: x + y))({'A': [1, 2, 3, 4]})
    10
    """
    return PipelineStep(
        FunctionApplication(
            functools.partial, _reduce, func, initial=initial  # type: ignore [arg-type]
        ),
        f"reduce({func!r})"
        if initial is MISSING
        else f"reduce({func!r}, initial={initial!r})",
    )
