import sys

if sys.version_info < (3, 10):
    from typing_extensions import ParamSpec
else:
    from typing import ParamSpec

import builtins
import functools
import itertools
from types import MappingProxyType
from typing import Any, Callable, Hashable, Iterable, Mapping, Tuple, TypeVar, Union

from ._missing import MISSING, MaybeMissing
from .application import PartialApplication
from .pipeline import Pipeline, PipelineStep, pipeline_step
from .types import Evaluatable, MaybeEvaluatable

A = TypeVar("A")
B = TypeVar("B")
K1 = TypeVar("K1", bound=Hashable)
K2 = TypeVar("K2", bound=Hashable)
V1 = TypeVar("V1")
V2 = TypeVar("V2")
P = ParamSpec("P")


def partial(
    __func: MaybeEvaluatable[Callable[P, A]],
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
    return PartialApplication(__func, *args, **kwargs)


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
    >>> (Option('A') >> F.map(lambda x: x + 1) >> list)({'A': [1, 2, 3, 4]})
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
    >>> (Option('A') >> F.filter(lambda x: x % 2 == 0) >> list)({'A': [1, 2, 3, 4]})
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


def into(
    func: MaybeEvaluatable[Callable[..., A]],
) -> PipelineStep[Union[Iterable, Mapping[str, Any]], A]:
    """Convert a function that takes positional arguments into one that takes an iterable.

    This can be useful if you have an evaluatable that returns an iterable of args or a mapping
    of kwargs and you want to unpack that into a function that takes positional or keyword
    arguments.

    Arguments
    ---------
    func : MaybeEvaluatable[Callable[..., A]]
        The function to apply to the arguments.
        Can be an evaluatable that returns a function or a constant function.

    Returns
    -------
    PipelineStep[Union[Iterable, Mapping[str, Any], A]
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
    def _into(
        args: Union[Iterable, Mapping[str, Any]],
        f: Callable[..., A] = func,  # type: ignore[assignment]
    ) -> A:
        return f(**args) if isinstance(args, Mapping) else f(*args)

    return PipelineStep(_into, f"into({func!r})")


def flatmap(
    func: MaybeEvaluatable[Callable[[A], Iterable[B]]],
) -> PipelineStep[Iterable[A], Iterable[B]]:
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
    >>> (Option('A') >> F.flatmap(lambda x: [x, x + 1]) >> list)({'A': [1, 2, 3, 4]})
    [1, 2, 2, 3, 3, 4, 4, 5]
    """
    return PipelineStep(
        map(func) + itertools.chain.from_iterable,
        f"flatmap({func!r})",
    )


def map_items(
    func: MaybeEvaluatable[Callable[[K1, V1], Tuple[K2, V2]]],
) -> PipelineStep[Mapping[K1, V1], Mapping[K2, V2]]:
    """Create a pipeline step that maps a function over the items of a mapping.

    Arguments
    ---------
    func : MaybeEvaluatable[Callable[[K1, V1], Tuple[K2, V2]]]
        The function to apply to each item of the mapping. This can be an
        Evaluatable that returns a function, or a constant function.

    Returns
    -------
    PipelineStep[Mapping[K1, V1], Mapping[K2, V2]]
        A pipeline step that applies the function to the items of the mapping.


    Example Usage
    -------------
    >>> from labrea import Option
    >>> import labrea.functions as F
    >>>
    >>> (Option('A') >> F.map_items(lambda k, v: (k + 1, v + 1)))({'A': {1: 2, 3: 4}})
    mappingproxy({2: 3, 4: 5})
    """
    return PipelineStep(
        (
            Pipeline()  # type: ignore
            + (lambda m: m.items())  # type: ignore
            + map(into(func))  # type: ignore
            + dict
            + MappingProxyType  # type: ignore
        ),
        f"map_items({func!r})",
    )


def map_keys(
    func: MaybeEvaluatable[Callable[[K1], K2]],
) -> PipelineStep[Mapping[K1, V1], Mapping[K2, V1]]:
    """Create a pipeline step that maps a function over the keys of a mapping.

    Arguments
    ---------
    func : MaybeEvaluatable[Callable[[K1], K2]]
        The function to apply to each key of the mapping. This can be an
        Evaluatable that returns a function, or a constant function.

    Returns
    -------
    PipelineStep[Mapping[K1, V1], Mapping[K2, V1]]
        A pipeline step that applies the function to the keys of the mapping.


    Example Usage
    -------------
    >>> from labrea import Option
    >>> import labrea.functions as F
    >>>
    >>> (Option('A') >> F.map_keys(lambda k: k + 1))({'A': {1: 2, 3: 4}})
    mappingproxy({2: 2, 4: 4})
    """
    return PipelineStep(
        map_items(partial(lambda k, v, f: (f(k), v), f=func)),
        f"map_keys({func!r})",
    )


def map_values(
    func: MaybeEvaluatable[Callable[[V1], V2]],
) -> PipelineStep[Mapping[K1, V1], Mapping[K1, V2]]:
    """Create a pipeline step that maps a function over the values of a mapping.

    Arguments
    ---------
    func : MaybeEvaluatable[Callable[[V1], V2]]
        The function to apply to each value of the mapping. This can be an
        Evaluatable that returns a function, or a constant function.

    Returns
    -------
    PipelineStep[Mapping[K1, V1], Mapping[K1, V2]]
        A pipeline step that applies the function to the values of the mapping.


    Example Usage
    -------------
    >>> from labrea import Option
    >>> import labrea.functions as F
    >>>
    >>> (Option('A') >> F.map_values(lambda v: v + 1))({'A': {1: 2, 3: 4}})
    mappingproxy({1: 3, 3: 5})
    """
    return PipelineStep(
        map_items(partial(lambda k, v, f: (k, f(v)), f=func)),
        f"map_values({func!r})",
    )


def filter_items(
    func: MaybeEvaluatable[Callable[[K1, V1], bool]],
) -> PipelineStep[Mapping[K1, V1], Mapping[K1, V1]]:
    """Create a pipeline step that filters items from a mapping using a predicate function.

    Arguments
    ---------
    func : MaybeEvaluatable[Callable[[K1, V1], bool]]
        The predicate function to apply to each item of the mapping. This can be an
        Evaluatable that returns a function, or a constant function.

    Returns
    -------
    PipelineStep[Mapping[K1, V1], Mapping[K1, V1]]
        A pipeline step that filters the items of the mapping using the predicate function.


    Example Usage
    -------------
    >>> from labrea import Option
    >>> import labrea.functions as F
    >>>
    >>> (Option('A') >> F.filter_items(lambda k, v: k % 2 == 0))({'A': {1: 2, 3: 4}})
    mappingproxy({3: 4})
    """
    return PipelineStep(
        (
            Pipeline()  # type: ignore
            + (lambda m: m.items())  # type: ignore
            + filter(into(func))  # type: ignore
            + dict
            + MappingProxyType  # type: ignore
        ),
        f"filter_items({func!r})",
    )


def filter_keys(
    func: MaybeEvaluatable[Callable[[K1], bool]],
) -> PipelineStep[Mapping[K1, V1], Mapping[K1, V1]]:
    """Create a pipeline step that filters keys from a mapping using a predicate function.

    Arguments
    ---------
    func : MaybeEvaluatable[Callable[[K1], bool]]
        The predicate function to apply to each key of the mapping. This can be an
        Evaluatable that returns a function, or a constant function.

    Returns
    -------
    PipelineStep[Mapping[K1, V1], Mapping[K1, V1]]
        A pipeline step that filters the keys of the mapping using the predicate function.


    Example Usage
    -------------
    >>> from labrea import Option
    >>> import labrea.functions as F
    >>>
    >>> (Option('A') >> F.filter_keys(lambda k: k % 2 == 0))({'A': {1: 2, 3: 4}})
    mappingproxy({1: 2})
    """
    return PipelineStep(
        filter_items(partial(lambda k, v, f: f(k), f=func)),
        f"filter_keys({func!r})",
    )


def filter_values(
    func: MaybeEvaluatable[Callable[[V1], bool]],
) -> PipelineStep[Mapping[K1, V1], Mapping[K1, V1]]:
    """Create a pipeline step that filters values from a mapping using a predicate function.

    Arguments
    ---------
    func : MaybeEvaluatable[Callable[[V1], bool]]
        The predicate function to apply to each value of the mapping. This can be an
        Evaluatable that returns a function, or a constant function.

    Returns
    -------
    PipelineStep[Mapping[K1, V1], Mapping[K1, V1]]
        A pipeline step that filters the values of the mapping using the predicate function.


    Example Usage
    -------------
    >>> from labrea import Option
    >>> import labrea.functions as F
    >>>
    >>> (Option('A') >> F.filter_values(lambda v: v % 2 == 0))({'A': {1: 2, 3: 4}})
    mappingproxy({1: 2})
    """
    return PipelineStep(
        filter_items(partial(lambda k, v, f: f(v), f=func)),
        f"filter_values({func!r})",
    )
