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

from . import collections
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


def eq(value: Any) -> PipelineStep[Any, bool]:
    """Create a pipeline step that checks if the input is equal to a value.

    Arguments
    ---------
    value : Any
        The value to compare the input to.

    Returns
    -------
    PipelineStep[Any, bool]
        A pipeline step that checks if the input is equal to the value.


    Example Usage
    -------------
    >>> from labrea import Option
    >>> import labrea.functions as F
    >>>
    >>> (Option('A') >> F.eq(1))({'A': 1})
    True
    """
    return PipelineStep(
        partial(lambda x, v: x == v, v=value),
        f"eq({value!r})",
    )


def ne(value: Any) -> PipelineStep[Any, bool]:
    """Create a pipeline step that checks if the input is not equal to a value.

    Arguments
    ---------
    value : Any
        The value to compare the input to.

    Returns
    -------
    PipelineStep[Any, bool]
        A pipeline step that checks if the input is not equal to the value.


    Example Usage
    -------------
    >>> from labrea import Option
    >>> import labrea.functions as F
    >>>
    >>> (Option('A') >> F.ne(1))({'A': 1})
    False
    """
    return PipelineStep(
        partial(lambda x, v: x != v, v=value),
        f"ne({value!r})",
    )


def gt(value: Any) -> PipelineStep[Any, bool]:
    """Create a pipeline step that checks if the input is greater than a value.

    Arguments
    ---------
    value : Any
        The value to compare the input to.

    Returns
    -------
    PipelineStep[Any, bool]
        A pipeline step that checks if the input is greater than the value.


    Example Usage
    -------------
    >>> from labrea import Option
    >>> import labrea.functions as F
    >>>
    >>> (Option('A') >> F.gt(1))({'A': 2})
    True
    """
    return PipelineStep(
        partial(lambda x, v: x > v, v=value),
        f"gt({value!r})",
    )


def ge(value: Any) -> PipelineStep[Any, bool]:
    """Create a pipeline step that checks if the input is greater than or equal to a value.

    Arguments
    ---------
    value : Any
        The value to compare the input to.

    Returns
    -------
    PipelineStep[Any, bool]
        A pipeline step that checks if the input is greater than or equal to the value.


    Example Usage
    -------------
    >>> from labrea import Option
    >>> import labrea.functions as F
    >>>
    >>> (Option('A') >> F.ge(1))({'A': 1})
    True
    """
    return PipelineStep(
        partial(lambda x, v: x >= v, v=value),
        f"ge({value!r})",
    )


def lt(value: Any) -> PipelineStep[Any, bool]:
    """Create a pipeline step that checks if the input is less than a value.

    Arguments
    ---------
    value : Any
        The value to compare the input to.

    Returns
    -------
    PipelineStep[Any, bool]
        A pipeline step that checks if the input is less than the value.


    Example Usage
    -------------
    >>> from labrea import Option
    >>> import labrea.functions as F
    >>>
    >>> (Option('A') >> F.lt(1))({'A': 0})
    True
    """
    return PipelineStep(
        partial(lambda x, v: x < v, v=value),
        f"lt({value!r})",
    )


def le(value: Any) -> PipelineStep[Any, bool]:
    """Create a pipeline step that checks if the input is less than or equal to a value.

    Arguments
    ---------
    value : Any
        The value to compare the input to.

    Returns
    -------
    PipelineStep[Any, bool]
        A pipeline step that checks if the input is less than or equal to the value.


    Example Usage
    -------------
    >>> from labrea import Option
    >>> import labrea.functions as F
    >>>
    >>> (Option('A') >> F.le(1))({'A': 1})
    True
    """
    return PipelineStep(
        partial(lambda x, v: x <= v, v=value),
        f"le({value!r})",
    )


def has_remainder(
    divisor: MaybeEvaluatable[int], reminder: MaybeEvaluatable[int]
) -> PipelineStep[int, bool]:
    """Create a pipeline step that checks if the input has a remainder when divided by a divisor.

    Arguments
    ---------
    divisor : MaybeEvaluatable[int]
        The divisor to divide the input by. This can be an Evaluatable that returns
        a divisor, or a constant divisor.
    reminder : MaybeEvaluatable[int]
        The reminder to check if the input has when divided by the divisor. This can
        be an Evaluatable that returns a reminder, or a constant reminder.

    Returns
    -------
    PipelineStep[int, bool]
        A pipeline step that checks if the input has a reminder when divided by the divisor.


    Example Usage
    -------------
    >>> from labrea import Option
    >>> import labrea.functions as F
    >>>
    >>> (Option('A') >> F.has_remainder(2, 1))({'A': 3})
    True
    """
    return PipelineStep(
        partial(
            lambda x, d, r: x % d == r,
            d=Evaluatable.ensure(divisor),
            r=Evaluatable.ensure(reminder),
        ),
        f"has_remainder({divisor!r}, {reminder!r})",
    )


positive = gt(0)
positive.__doc__ = "A pipeline step that checks if the input is positive."
negative = lt(0)
negative.__doc__ = "A pipeline step that checks if the input is negative."
non_positive = le(0)
non_positive.__doc__ = "A pipeline step that checks if the input is non-positive."
non_negative = ge(0)
non_negative.__doc__ = "A pipeline step that checks if the input is non-negative."
is_even = has_remainder(2, 0)
is_even.__doc__ = "A pipeline step that checks if the input is even."
is_odd = has_remainder(2, 1)
is_odd.__doc__ = "A pipeline step that checks if the input is odd."


def instance_of(*types: MaybeEvaluatable[type]) -> PipelineStep[Any, bool]:
    """Create a pipeline step that checks if the input is an instance of a type.

    Arguments
    ---------
    *types : MaybeEvaluatable[type]
        The types to check if the input is an instance of. These can be
        Evaluatables that return types, or constant types.

    Returns
    -------
    PipelineStep[Any, bool]
        A pipeline step that checks if the input is an instance of the type.


    Example Usage
    -------------
    >>> from labrea import Option
    >>> import labrea.functions as F
    >>>
    >>> (Option('A') >> F.instance_of(int))({'A': 1})
    True
    """
    return PipelineStep(
        partial(
            lambda x, t: isinstance(x, t),
            t=collections.evaluatable_tuple(
                *builtins.map(Evaluatable.ensure, types)  # type: ignore [arg-type]
            ),
        ),
        f"instance_of({', '.join(builtins.map(repr, types))})",
    )


def all(*funcs: MaybeEvaluatable[Callable[[Any], bool]]) -> PipelineStep[Any, bool]:
    """Create a pipeline step that checks if all functions return True for the input.

    Arguments
    ---------
    *funcs : MaybeEvaluatable[Callable[[Any], bool]]
        The functions to apply to the input. These can be Evaluatables that return
        functions, or constant functions.

    Returns
    -------
    PipelineStep[Any, bool]
        A pipeline step that checks if all functions return True for the input.


    Example Usage
    -------------
    >>> from labrea import Option
    >>> import labrea.functions as F
    >>>
    >>> (Option('A') >> F.all(lambda x: x > 0, lambda x: x < 10))({'A': 5})
    True
    """
    return PipelineStep(
        partial(
            lambda x, fs: builtins.all(f(x) for f in fs),
            fs=collections.evaluatable_tuple(
                *builtins.map(Evaluatable.ensure, funcs)  # type: ignore [arg-type]
            ),
        ),
        f"all({', '.join(builtins.map(repr, funcs))})",
    )


def any(*funcs: MaybeEvaluatable[Callable[[Any], bool]]) -> PipelineStep[Any, bool]:
    """Create a pipeline step that checks if any functions return True for the input.

    Arguments
    ---------
    *funcs : MaybeEvaluatable[Callable[[Any], bool]]
        The functions to apply to the input. These can be Evaluatables that return
        functions, or constant functions.

    Returns
    -------
    PipelineStep[Any, bool]
        A pipeline step that checks if any functions return True for the input.


    Example Usage
    -------------
    >>> from labrea import Option
    >>> import labrea.functions as F
    >>>
    >>> (Option('A') >> F.any(lambda x: x < 0, lambda x: x > 10))({'A': 5})
    False
    """
    return PipelineStep(
        partial(
            lambda x, fs: builtins.any(f(x) for f in fs),
            fs=collections.evaluatable_tuple(
                *builtins.map(Evaluatable.ensure, funcs)  # type: ignore [arg-type]
            ),
        ),
        f"any({', '.join(builtins.map(repr, funcs))})",
    )


def is_not(func: MaybeEvaluatable[Callable[[Any], bool]]) -> PipelineStep[Any, bool]:
    """Create a pipeline step that negates the result of a function.

    Arguments
    ---------
    func : MaybeEvaluatable[Callable[[Any], bool]]
        The function to negate the result of. This can be an Evaluatable that
        returns a function, or a constant function.

    Returns
    -------
    PipelineStep[Any, bool]
        A pipeline step that negates the result of the function.


    Example Usage
    -------------
    >>> from labrea import Option
    >>> import labrea.functions as F
    >>>
    >>> (Option('A') >> F.not(lambda x: x < 0))({'A': 5})
    True
    """
    return PipelineStep(
        partial(lambda x, f: not f(x), f=Evaluatable.ensure(func)),
        f"is_not({func!r})",
    )
