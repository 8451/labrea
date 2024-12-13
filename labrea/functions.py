import sys

if sys.version_info < (3, 10):
    from typing_extensions import ParamSpec
else:
    from typing import ParamSpec

import builtins
import functools
import itertools
from typing import Callable, Iterable, TypeVar

from ._missing import MISSING, MaybeMissing
from .application import PartialApplication
from .pipeline import Pipeline, PipelineStep, pipeline_step
from .types import Evaluatable, MaybeEvaluatable

A = TypeVar("A")
B = TypeVar("B")
P = ParamSpec("P")


def partial(
    func: MaybeEvaluatable[Callable[P, A]],
    *args: MaybeEvaluatable["P.args"],
    **kwargs: MaybeEvaluatable["P.kwargs"],
) -> Evaluatable[Callable[..., A]]:
    """Analog of functools.partial that works with Evaluatables.

    Arguments
    ----------
    func : MaybeEvaluatable[Callable[P, A]]
        The function to partially apply.
    *args : MaybeEvaluatable[P.args]
        The positional arguments to partially apply to the function. These
        can be Evaluatables that return values, or constant values.
    **kwargs : MaybeEvaluatable[P.kwargs]
        The keyword arguments to partially apply to the function. These can
        be Evaluatables that return values, or constant values.

    Returns
    -------
    Evaluatable[Callable[..., A]]
        An Evaluatable that returns a partially applied function.

    Example Usage
    -------------
    >>> from labrea import Option
    >>> import labrea.functions as F
    >>>
    >>> (Option('A') >> F.partial(lambda x, y: x + y, y=Option('B')))({'A': 1, 'B': 2})
    3
    """
    return PartialApplication(func, *args, **kwargs)


def map(
    func: MaybeEvaluatable[Callable[[A], B]],
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
        partial(builtins.map, func),  # type: ignore [arg-type]
        f"map({func!r})",
    )


def filter(
    func: MaybeEvaluatable[Callable[[A], bool]],
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
        partial(builtins.filter, func),  # type: ignore [arg-type]
        f"filter({func!r})",
    )


def _reduce(
    func: Callable[[A, B], A], iterable: Iterable[B], initial: MaybeMissing[A]
) -> A:
    if initial is MISSING:
        return functools.reduce(func, iterable)  # type: ignore

    return functools.reduce(func, iterable, initial)


def reduce(
    func: MaybeEvaluatable[Callable[[A, B], A]],
    initial: MaybeMissing[MaybeEvaluatable[A]] = MISSING,
) -> PipelineStep[Iterable[B], A]:
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
        partial(_reduce, func, initial=initial),
        f"reduce({func!r})"
        if initial is MISSING
        else f"reduce({func!r}, initial={initial!r})",
    )  # type: ignore [arg-type]


def into(func: MaybeEvaluatable[Callable[..., A]]) -> PipelineStep[Iterable, A]:
    """Convert a function that takes positional arguments into one that takes an iterable.

    This can be useful if you have an evaluatable that returns a tuple of arguments and you want
    to unpack that tuple into a function that takes positional arguments.

    Arguments
    ---------
    func : MaybeEvaluatable[Callable[..., A]]
        The function to apply to the arguments.
        Can be an evaluatable that returns a function or a constant function.

    Returns
    -------
    PipelineStep[Iterable, A]
        A pipeline step that applies the function to the arguments after unpacking.


    Example Usage
    -------------
    >>> from labrea import Option
    >>> import labrea.functions as F
    >>>
    >>> (Option('A') >> F.into(lambda x, y: x + y))({'A': [1, 2]})
    3
    """

    @pipeline_step
    def _into(args: Iterable, f: Callable[..., A] = func) -> A:  # type: ignore[assignment]
        return f(*args)

    return _into


def flatmap(
    func: MaybeEvaluatable[Callable[[A], Iterable[B]]],
) -> Pipeline[Iterable[A], Iterable[B]]:
    """Create a pipeline step that maps a function over an iterable and flattens the result.

    This allows for calling flatmap in a functional style over an iterable
    using the :code:`.apply()` method or the :code:`>>` operator on an
    Evaluatable object that returns an iterable.

    Arguments
    ----------
    func : MaybeEvaluatable[Callable[[A], Iterable[B]]]
        The function to apply to each element of the iterable. This can be
        an Evaluatable that returns a function, or a constant function.


    Example Usage
    -------------
    >>> from labrea import Option
    >>> import labrea.functions as F
    >>>
    >>> (Option('A') >> F.flatmap(lambda x: [x, x + 1]))({'A': [1, 2, 3, 4]})
    [1, 2, 2, 3, 3, 4, 4, 5]
    """
    return map(func) + itertools.chain.from_iterable
