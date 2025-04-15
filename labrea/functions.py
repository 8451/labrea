import sys

if sys.version_info < (3, 10):
    from typing_extensions import ParamSpec
else:
    from typing import ParamSpec

import builtins
import functools
import itertools
import typing
from types import MappingProxyType
from typing import (
    Any,
    Callable,
    Container,
    Hashable,
    Iterable,
    Mapping,
    Protocol,
    Set,
    Tuple,
    TypeVar,
    Union,
)

from . import collections
from ._missing import MISSING, MaybeMissing, Missing
from .application import PartialApplication
from .pipeline import Pipeline, PipelineStep, pipeline_step
from .types import Evaluatable, MaybeEvaluatable

A = TypeVar("A")
B = TypeVar("B")
H = TypeVar("H", bound=Hashable)
K1 = TypeVar("K1", bound=Hashable)
K2 = TypeVar("K2", bound=Hashable)
V1 = TypeVar("V1")
V2 = TypeVar("V2")
P = ParamSpec("P")
X = TypeVar("X", contravariant=True)
Y = TypeVar("Y", covariant=True)
Z = TypeVar("Z")


class _Addable(Protocol[X, Y]):
    def __add__(self, __other: X) -> Y: ...


class _Subtractable(Protocol[X, Y]):
    def __sub__(self, __other: X) -> Y: ...


class _Multiplicable(Protocol[X, Y]):
    def __mul__(self, __other: X) -> Y: ...


class _Divisible(Protocol[X, Y]):
    def __truediv__(self, __other: X) -> Y: ...


class _Negatable(Protocol[Y]):
    def __neg__(self) -> Y: ...


class _Modable(Protocol[X, Y]):
    def __mod__(self, __other: X) -> Y: ...


class _Indexable(Protocol[X, Y]):
    def __getitem__(self, __index: X) -> Y: ...


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


def _flatten(
    iterable: Iterable[Iterable[Y]],
) -> Iterable[Y]:
    """Flatten an iterable of iterables into a single iterable."""
    return itertools.chain.from_iterable(iterable)


flatten = PipelineStep(Evaluatable.ensure(_flatten), "flatten")
flatten.__doc__ = """Create a pipeline step that flattens an iterable of iterables."""


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


def concat(
    iterable: MaybeEvaluatable[Iterable[A]],
) -> PipelineStep[Iterable[B], Iterable[Union[A, B]]]:
    """Create a pipeline step that concatenates an iterable to another iterable.

    Arguments
    ---------
    iterable : MaybeEvaluatable[Iterable[A]]
        The iterable to concatenate to the input. This can be an Evaluatable that
        returns an iterable, or a constant iterable.

    Returns
    -------
    PipelineStep[Iterable[A], Iterable[A]]
        A pipeline step that concatenates the input with the iterable.


    Example Usage
    -------------
    >>> from labrea import Option
    >>> import labrea.functions as F
    >>>
    >>> (Option('A') >> F.append([4, 5, 6]))({'A': [1, 2, 3]})
    [1, 2, 3, 4, 5, 6]
    """
    return PipelineStep(
        partial(lambda x, i: itertools.chain(x, i), i=Evaluatable.ensure(iterable)),
        f"append({iterable!r})",
    )


def append(
    item: MaybeEvaluatable[A],
) -> PipelineStep[Iterable[B], Iterable[Union[A, B]]]:
    """Create a pipeline step that appends an item to an iterable.

    Arguments
    ---------
    item : MaybeEvaluatable[A]
        The item to append to the input. This can be an Evaluatable that returns
        an item, or a constant item.

    Returns
    -------
    PipelineStep[Iterable[A], Iterable[A]]
        A pipeline step that appends the item to the input.


    Example Usage
    -------------
    >>> from labrea import Option
    >>> import labrea.functions as F
    >>>
    >>> (Option('A') >> F.append(4))({'A': [1, 2, 3]})
    [1, 2, 3, 4]
    """
    return PipelineStep(
        concat(collections.evaluatable_tuple(Evaluatable.ensure(item))),  # type: ignore[arg-type]
        f"append({item!r})",
    )


def intersect(
    collection: MaybeEvaluatable[Iterable[H]],
) -> PipelineStep[Iterable[H], Set[H]]:
    """Create a pipeline step that intersects an iterable with another collection.

    Arguments
    ---------
    collection : MaybeEvaluatable[Iterable[H]]
        The collection to intersect with the input. This can be an Evaluatable that
        returns a collection, or a constant collection.

    Returns
    -------
    PipelineStep[Iterable[H], Set[H]]
        A pipeline step that intersects the input with the collection.


    Example Usage
    -------------
    >>> from labrea import Option
    >>> import labrea.functions as F
    >>>
    >>> (Option('A') >> F.intersect([1, 2, 3]))({'A': [2, 3, 4]})
    {2, 3}
    """
    return PipelineStep(
        partial(lambda x, c: set(x) & set(c), c=Evaluatable.ensure(collection)),
        f"intersect({collection!r})",
    )


def union(
    collection: MaybeEvaluatable[Iterable[H]],
) -> PipelineStep[Iterable[H], Set[H]]:
    """Create a pipeline step that unions an iterable with another collection.

    Arguments
    ---------
    collection : MaybeEvaluatable[Iterable[H]]
        The collection to union with the input. This can be an Evaluatable that
        returns a collection, or a constant collection.

    Returns
    -------
    PipelineStep[Iterable[H], Set[H]]
        A pipeline step that unions the input with the collection.


    Example Usage
    -------------
    >>> from labrea import Option
    >>> import labrea.functions as F
    >>>
    >>> (Option('A') >> F.union([1, 2, 3]))({'A': [2, 3, 4]})
    {1, 2, 3, 4}
    """
    return PipelineStep(
        partial(lambda x, c: set(x) | set(c), c=Evaluatable.ensure(collection)),
        f"union({collection!r})",
    )


def difference(
    collection: MaybeEvaluatable[Iterable[H]],
) -> PipelineStep[Iterable[H], Set[H]]:
    """Create a pipeline step that computes the difference between sets.

    Arguments
    ---------
    collection : MaybeEvaluatable[Iterable[H]]
        The collection to compute the difference with the input. This can be an Evaluatable
        that returns a collection, or a constant collection.

    Returns
    -------
    PipelineStep[Iterable[H], Set[H]]
        A pipeline step that computes the difference between the input and the collection.


    Example Usage
    -------------
    >>> from labrea import Option
    >>> import labrea.functions as F
    >>>
    >>> (Option('A') >> F.difference([1, 2, 3]))({'A': [2, 3, 4]})
    {4}
    """
    return PipelineStep(
        partial(lambda x, c: set(x) - set(c), c=Evaluatable.ensure(collection)),
        f"difference({collection!r})",
    )


def symmetric_difference(
    collection: MaybeEvaluatable[Iterable[H]],
) -> PipelineStep[Iterable[H], Set[H]]:
    """Create a pipeline step that computes the symmetric difference between sets.

    Arguments
    ---------
    collection : MaybeEvaluatable[Iterable[H]]
        The collection to compute the symmetric difference with the input. This can be an
        Evaluatable that returns a collection, or a constant collection.

    Returns
    -------
    PipelineStep[Iterable[H], Set[H]]
        A pipeline step that computes the symmetric difference between the input and the collection.


    Example Usage
    -------------
    >>> from labrea import Option
    >>> import labrea.functions as F
    >>>
    >>> (Option('A') >> F.symmetric_difference([1, 2, 3]))({'A': [2, 3, 4]})
    {1, 4}
    """
    return PipelineStep(
        partial(lambda x, c: set(x) ^ set(c), c=Evaluatable.ensure(collection)),
        f"symmetric_difference({collection!r})",
    )


def _get(container: _Indexable[X, Y], key: X, default: MaybeMissing[Z]) -> Union[Y, Z]:
    try:
        return container[key]
    except (KeyError, IndexError) as e:
        if default is MISSING:
            raise e
        return default


@typing.overload
def get(
    __x: MaybeEvaluatable[X], default: Missing = MISSING
) -> PipelineStep[_Indexable[X, Y], Y]: ...


@typing.overload
def get(
    __x: MaybeEvaluatable[X], default: Z
) -> PipelineStep[_Indexable[X, Y], Union[Y, Z]]: ...


def get(
    __x: MaybeEvaluatable[X], default: MaybeMissing[Z] = MISSING
) -> PipelineStep[_Indexable[X, Y], Union[Y, Z]]:
    """Create a pipeline step that gets a value from the input at the given key/index

    Arguments
    ---------
    __x : X
        The key/index to get the value from the input. This can be an Evaluatable that returns a value,
        or a constant value.
    default : MaybeMissing[Y], optional
        The default value to return if the key/index is not found in the input. This can be an
        Evaluatablethat returns a value, or a constant value. If not provided, an exception will
        be raised if the key/index is not found.

    Returns
    -------
    PipelineStep[_Indexable[X, Y], Y]
        A pipeline step that gets the value from the input at the given key/index.


    Example Usage
    -------------
    >>> from labrea import Option
    >>> import labrea.functions as F
    >>>
    >>> (Option('A') >> F.get(1))({'A': ['a', 'b', 'c'])]
    'b'
    """
    return PipelineStep(
        partial(_get, key=__x, default=default),
        f"get({__x!r})",
    )


@typing.overload
def get_from(
    __x: MaybeEvaluatable[_Indexable[X, Y]], default: Missing
) -> PipelineStep[X, Y]: ...


@typing.overload
def get_from(
    __x: MaybeEvaluatable[_Indexable[X, Y]], default: Z
) -> PipelineStep[X, Union[Y, Z]]: ...


def get_from(
    __x: MaybeEvaluatable[_Indexable[X, Y]], default: MaybeMissing[Z] = MISSING
) -> PipelineStep[X, Union[Y, Z]]:
    """Create a pipeline step that gets a value from the input at the given key/index from the left.

    This will reverse the operand order compared to :code:`get`.

    Arguments
    ---------
    __x : _Indexable[X, Y]
        The key/index to get the value from the input. This can be an Evaluatable that returns a value,
        or a constant value.
    default : MaybeMissing[Z], optional
        The default value to return if the key/index is not found in the input. This can be an Evaluatable

    Returns
    -------
    PipelineStep[X, Y]
        A pipeline step that gets the value from the input at the given key/index.


    Example Usage
    -------------
    >>> from labrea import Option
    >>> import labrea.functions as F
    >>>
    >>> (Option('A') >> F.get_from(['a', 'b', 'c']))({'A': 1})
    'b'
    """
    return PipelineStep(
        partial(_get, __x, default=default),
        f"get_from({__x!r})",
    )


def add(__x: MaybeEvaluatable[_Addable[X, Y]]) -> PipelineStep[X, Y]:
    """Create a pipeline step that adds a value to the input.

    Arguments
    ---------
    __x : _Addable[X, Y]
        The value to add to the input. This can be an Evaluatable that returns a value,
        or a constant value.

    Returns
    -------
    PipelineStep[X, Y]
        A pipeline step that adds the value to the input.


    Example Usage
    -------------
    >>> from labrea import Option
    >>> import labrea.functions as F
    >>>
    >>> (Option('A') >> F.add(1))({'A': 2})
    3
    """
    return PipelineStep(
        partial(lambda left, right: left + right, right=Evaluatable.ensure(__x)),
        f"add({__x!r})",
    )


def subtract(__x: MaybeEvaluatable[_Subtractable[X, Y]]) -> PipelineStep[X, Y]:
    """Create a pipeline step that subtracts a value from the input.

    Arguments
    ---------
    __x : _Subtractable[X, Y]
        The value to subtract from the input. This can be an Evaluatable that returns a value,
        or a constant value.

    Returns
    -------
    PipelineStep[X, Y]
        A pipeline step that subtracts the value from the input.


    Example Usage
    -------------
    >>> from labrea import Option
    >>> import labrea.functions as F
    >>>
    >>> (Option('A') >> F.subtract(1))({'A': 2})
    1
    """
    return PipelineStep(
        partial(lambda left, right: left - right, right=Evaluatable.ensure(__x)),
        f"subtract({__x!r})",
    )


def multiply(__x: MaybeEvaluatable[_Multiplicable[X, Y]]) -> PipelineStep[X, Y]:
    """Create a pipeline step that multiplies the input by a value.

    Arguments
    ---------
    __x : _Multiplicable[X, Y]
        The value to multiply the input by. This can be an Evaluatable that returns a value,
        or a constant value.

    Returns
    -------
    PipelineStep[X, Y]
        A pipeline step that multiplies the input by the value.


    Example Usage
    -------------
    >>> from labrea import Option
    >>> import labrea.functions as F
    >>>
    >>> (Option('A') >> F.multiply(2))({'A': 3})
    6
    """
    return PipelineStep(
        partial(lambda left, right: left * right, right=Evaluatable.ensure(__x)),
        f"multiply({__x!r})",
    )


def left_multiply(__x: MaybeEvaluatable[X]) -> PipelineStep[_Multiplicable[X, Y], Y]:
    """Create a pipeline step that multiplies the input by a value from the left.

    This will reverse the operand order compared to :code:`multiply`, which is useful
    when multiplacation is not commutative.

    Arguments
    ---------
    __x : X
        The value to multiply the input by. This can be an Evaluatable that returns a value,
        or a constant value.

    Returns
    -------
    PipelineStep[_Multiplicable[X, Y], Y]
        A pipeline step that multiplies the input by the value.


    Example Usage
    -------------
    >>> from labrea import Option
    >>> import labrea.functions as F
    >>>
    >>> (Option('A') >> F.multiply_by(2))({'A': 3})
    6
    """
    return PipelineStep(
        partial(lambda left, right: left * right, Evaluatable.ensure(__x)),
        f"left_multiply({__x!r})",
    )


def divide_by(__x: MaybeEvaluatable[_Divisible[X, Y]]) -> PipelineStep[X, Y]:
    """Create a pipeline step that divides the input by a value.

    Arguments
    ---------
    __x : _Divisible[X, Y]
        The value to divide the input by. This can be an Evaluatable that returns a value,
        or a constant value.

    Returns
    -------
    PipelineStep[X, Y]
        A pipeline step that divides the input by the value.


    Example Usage
    -------------
    >>> from labrea import Option
    >>> import labrea.functions as F
    >>>
    >>> (Option('A') >> F.divide(2))({'A': 6})
    3
    """
    return PipelineStep(
        partial(lambda left, right: left / right, right=Evaluatable.ensure(__x)),
        f"divide_by({__x!r})",
    )


def divide_into(__x: MaybeEvaluatable[X]) -> PipelineStep[_Divisible[X, Y], Y]:
    """Create a pipeline step that divides the input into a value from the left.

    This will reverse the operand order compared to :code:`divide`.

    Arguments
    ---------
    __x : X
        The value to divide the input into. This can be an Evaluatable that returns a value,
        or a constant value.

    Returns
    -------
    PipelineStep[_Divisible[X, Y], Y]
        A pipeline step that divides the input by the value.


    Example Usage
    -------------
    >>> from labrea import Option
    >>> import labrea.functions as F
    >>>
    >>> (Option('A') >> F.divide_into(2))({'A': 6})
    3
    """
    return PipelineStep(
        partial(lambda left, right: left / right, Evaluatable.ensure(__x)),
        f"divide_into({__x!r})",
    )


def _negate(__x: _Negatable[Y]) -> Y:
    return -__x


negate = PipelineStep(Evaluatable.ensure(_negate), "negate")
negate.__doc__ = """Pipeline step that negates the input."""


def modulo(__x: MaybeEvaluatable[X]) -> PipelineStep[_Modable[X, Y], Y]:
    """Create a pipeline step that computes the modulo of the input with a value.

    Arguments
    ---------
    __x : _Modable[X, Y]
        The value to compute the modulo with. This can be an Evaluatable that returns a value,
        or a constant value.

    Returns
    -------
    PipelineStep[_Modable[X, Y], Y]
        A pipeline step that computes the modulo of the input with the value.


    Example Usage
    -------------
    >>> from labrea import Option
    >>> import labrea.functions as F
    >>>
    >>> (Option('A') >> F.modulo(2))({'A': 5})
    1
    """
    return PipelineStep(
        partial(lambda left, right: left % right, right=Evaluatable.ensure(__x)),
        f"modulo({__x!r})",
    )


def merge(
    mapping: MaybeEvaluatable[Mapping[K1, V1]],
) -> PipelineStep[Mapping[K2, V2], Mapping[Union[K1, K2], Union[V1, V2]]]:
    """Create a pipeline step that merges a mapping with another mapping.

    Arguments
    ---------
    mapping : MaybeEvaluatable[Mapping[K1, K2]]
        The mapping to merge with the input. This can be an Evaluatable that
        returns a mapping, or a constant mapping.

    Returns
    -------
    PipelineStep[Mapping[K1, V1], Mapping[K2, V1]]
        A pipeline step that merges the input with the mapping.


    Example Usage
    -------------
    >>> from labrea import Option
    >>> import labrea.functions as F
    >>>
    >>> (Option('A') >> F.merge({'A': 'B'}))({'A': {'A': 1, 'B': 2}})
    {'B': 1}
    """
    return PipelineStep(
        partial(lambda x, m: {**x, **m}, m=Evaluatable.ensure(mapping)),
        f"merge({mapping!r})",
    )


length = PipelineStep(Evaluatable.ensure(len), "length")
length.__doc__ = """Create a pipeline step that computes the length of a sequence."""


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


def invert(
    func: MaybeEvaluatable[Callable[[Any], bool]] = lambda _: _,
) -> PipelineStep[Any, bool]:
    """Create a pipeline step that negates the result of a function.

    Arguments
    ---------
    func : MaybeEvaluatable[Callable[[Any], bool]], optional
        The function to negate the result of. This can be an Evaluatable that
        returns a function, or a constant function. If omitted, the identity
        function is used

    Returns
    -------
    PipelineStep[Any, bool]
        A pipeline step that negates the result of the function.


    Example Usage
    -------------
    >>> from labrea import Option
    >>> import labrea.functions as F
    >>>
    >>> (Option('A') >> F.invert(lambda x: x < 0))({'A': 5})
    True
    >>> (Option('A') >> F.invert())({'A': True})
    False
    """
    return PipelineStep(
        partial(lambda x, f: not f(x), f=Evaluatable.ensure(func)),
        f"is_not({func!r})",
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
    divisor: MaybeEvaluatable[X], reminder: MaybeEvaluatable[Y]
) -> PipelineStep[_Modable[X, Y], bool]:
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
even = has_remainder(2, 0)
even.__doc__ = "A pipeline step that checks if the input is even."
odd = has_remainder(2, 1)
odd.__doc__ = "A pipeline step that checks if the input is odd."
is_none = PipelineStep(Evaluatable.ensure(lambda x: x is None), "is_none")
is_none.__doc__ = "A pipeline step that checks if the input is None."
is_not_none = PipelineStep(invert(is_none), "is_not_none")
is_not_none.__doc__ = "A pipeline step that checks if the input is not None."


def is_in(container: MaybeEvaluatable[Container[A]]) -> PipelineStep[A, bool]:
    """Create a pipeline step that checks if the input is in a container.

    Arguments
    ---------
    container : MaybeEvaluatable[Container[A]]
        The container to check if the input is in. This can be an Evaluatable that
        returns a container, or a constant container.

    Returns
    -------
    PipelineStep[A, bool]
        A pipeline step that checks if the input is in the container.


    Example Usage
    -------------
    >>> from labrea import Option
    >>> import labrea.functions as F
    >>>
    >>> (Option('A') >> F.is_in([1, 2, 3]))({'A': 2})
    True
    """
    return PipelineStep(
        partial(lambda x, c: x in c, c=Evaluatable.ensure(container)),
        f"is_in({container!r})",
    )


def is_not_in(container: MaybeEvaluatable[Container[A]]) -> PipelineStep[A, bool]:
    """Create a pipeline step that checks if the input is not in a container.

    Arguments
    ---------
    container : MaybeEvaluatable[Container[A]]
        The container to check if the input is in. This can be an Evaluatable that
        returns a container, or a constant container.

    Returns
    -------
    PipelineStep[A, bool]
        A pipeline step that checks if the input is not in the container.


    Example Usage
    -------------
    >>> from labrea import Option
    >>> import labrea.functions as F
    >>>
    >>> (Option('A') >> F.is_in([1, 2, 3]))({'A': 4})
    True
    """
    return PipelineStep(
        invert(is_in(container)),
        f"is_not_in({container!r})",
    )


def one_of(*items: MaybeEvaluatable[A]) -> PipelineStep[A, bool]:
    """Create a pipeline step that checks if the input is one of the items.

    Arguments
    ---------
    *items : MaybeEvaluatable[A]
        The items to check if the input is one of. These can be Evaluatables that
        return items, or constant items.

    Returns
    -------
    PipelineStep[A, bool]
        A pipeline step that checks if the input is one of the items.


    Example Usage
    -------------
    >>> from labrea import Option
    >>> import labrea.functions as F
    >>>
    >>> (Option('A') >> F.one_of(1, 2, 3))({'A': 2})
    True
    """
    return PipelineStep(
        partial(
            lambda x, items: x in items,
            items=collections.evaluatable_tuple(
                *builtins.map(Evaluatable.ensure, items)  # type: ignore [arg-type]
            ),
        ),
        f"one_of({', '.join(builtins.map(repr, items))})",
    )


def none_of(*items: MaybeEvaluatable[A]) -> PipelineStep[A, bool]:
    """Create a pipeline step that checks if the input is none of the items.

    Arguments
    ---------
    *items : MaybeEvaluatable[A]
        The items to check if the input is one of. These can be Evaluatables that
        return items, or constant items.

    Returns
    -------
    PipelineStep[A, bool]
        A pipeline step that checks if the input is none of the items.


    Example Usage
    -------------
    >>> from labrea import Option
    >>> import labrea.functions as F
    >>>
    >>> (Option('A') >> F.none_of(1, 2, 3))({'A': 4})
    True
    """
    return PipelineStep(
        invert(one_of(*items)),
        f"none_of({', '.join(builtins.map(repr, items))})",
    )


def contains(value: MaybeEvaluatable[A]) -> PipelineStep[Container[A], bool]:
    """Create a pipeline step that checks if the container contains a value.

    Arguments
    ---------
    value : MaybeEvaluatable[A]
        The value to check if the container contains. This can be an Evaluatable
        that returns a value, or a constant value.

    Returns
    -------
    PipelineStep[Container[A], bool]
        A pipeline step that checks if the container contains the value.


    Example Usage
    -------------
    >>> from labrea import Option
    >>> import labrea.functions as F
    >>>
    >>> (Option('A') >> F.contains(2))({'A': [1, 2, 3]})
    True
    """
    return PipelineStep(
        partial(lambda c, v: v in c, v=Evaluatable.ensure(value)),
        f"contains({value!r})",
    )


def does_not_contain(value: MaybeEvaluatable[A]) -> PipelineStep[Container[A], bool]:
    """Create a pipeline step that checks if the container does not contain a value.

    Arguments
    ---------
    value : MaybeEvaluatable[A]
        The value to check if the container contains. This can be an Evaluatable
        that returns a value, or a constant value.

    Returns
    -------
    PipelineStep[Container[A], bool]
        A pipeline step that checks if the container does not contain the value.


    Example Usage
    -------------
    >>> from labrea import Option
    >>> import labrea.functions as F
    >>>
    >>> (Option('A') >> F.does_not_contain(4))({'A': [1, 2, 3]})
    True
    """
    return PipelineStep(
        invert(contains(value)),
        f"does_not_contain({value!r})",
    )


def intersects(
    iterable: MaybeEvaluatable[Iterable[H]],
) -> PipelineStep[Iterable[H], bool]:
    """Create a pipeline step that checks if the iterable intersects with another iterable.

    Arguments
    ---------
    container : MaybeEvaluatable[Iterable[H]]
        The iterable to check if the input intersects with. This can be an Evaluatable
        that returns a iterable, or a constant iterable.

    Returns
    -------
    PipelineStep[Iterable[H], bool]
        A pipeline step that checks if the input intersects with the iterable.


    Example Usage
    -------------
    >>> from labrea import Option
    >>> import labrea.functions as F
    >>>
    >>> (Option('A') >> F.intersects([1, 2, 3]))({'A': [2, 3, 4]})
    True
    """
    return PipelineStep(
        intersect(iterable) + bool,
        f"intersects({iterable!r})",
    )


def disjoint_from(
    iterable: MaybeEvaluatable[Iterable[H]],
) -> PipelineStep[Iterable[H], bool]:
    """Create a pipeline step that checks if the iterable is disjoint from another iterable.

    Arguments
    ---------
    container : MaybeEvaluatable[Iterable[A]]
        The iterable to check if the input is disjoint from. This can be an Evaluatable
        that returns a iterable, or a constant iterable.

    Returns
    -------
    PipelineStep[Iterable[A], bool]
        A pipeline step that checks if the input is disjoint from the iterable.


    Example Usage
    -------------
    >>> from labrea import Option
    >>> import labrea.functions as F
    >>>
    >>> (Option('A') >> F.disjoint_from([1, 2, 3]))({'A': [4, 5, 6]})
    True
    """
    return PipelineStep(
        invert(intersects(iterable)),
        f"disjoint_from({iterable!r})",
    )


def _ensure(value: A, predicate: Callable[[A], bool], msg: str) -> A:
    assert predicate(value), msg
    return value


def ensure(
    __predicate: MaybeEvaluatable[Callable[[A], bool]],
    __msg: MaybeMissing[MaybeEvaluatable[str]] = MISSING,
) -> PipelineStep[A, A]:
    """Create a pipeline step that checks if the input satisfies a predicate.

    Arguments
    ---------
    __predicate : MaybeEvaluatable[Callable[[A], bool]]
        The predicate to check if the input satisfies. This can be an Evaluatable
        that returns a predicate, or a constant predicate.
    __msg : MaybeMissing[MaybeEvaluatable[str]], optional
        The message to use if the predicate fails. This can be an Evaluatable
        that returns a message, or a constant message. If not provided, a default
        message will be used.

    Returns
    -------
    PipelineStep[A, A]
        A pipeline step that checks if the input satisfies the predicate.


    Example Usage
    -------------
    >>> from labrea import Option
    >>> import labrea.functions as F
    >>>
    >>> (Option('A') >> F.ensure(lambda x: x > 0))({'A': 1})
    1
    """
    __msg = __msg if __msg is not MISSING else f"Predicate {__predicate!r} failed"
    return PipelineStep(
        partial(
            _ensure,
            predicate=Evaluatable.ensure(__predicate),
            msg=Evaluatable.ensure(__msg),
        ),
        f"ensure({__predicate!r})",
    )


def get_attribute(__name: MaybeEvaluatable[str]) -> PipelineStep[Any, Any]:
    """Create a pipeline step that gets an attribute from the input.

    Arguments
    ---------
    __name : MaybeEvaluatable[str]
        The name of the attribute to get. This can be an Evaluatable that returns a string,
        or a constant string.

    Returns
    -------
    PipelineStep[Any, Any]
        A pipeline step that gets the attribute from the input.


    Example Usage
    -------------
    >>> from labrea import Option
    >>> import labrea.functions as F
    >>>
    >>> (Option('A') >> F.get_attribute('upper'))({'A': 'hello'})
    'HELLO'
    """
    return PipelineStep(
        partial(lambda name, obj: getattr(obj, name), __name),
        f"get_attribute({__name!r})",
    )


def _call_method(name: str, args: tuple, kwargs: dict, obj: Any) -> Any:
    return getattr(obj, name)(*args, **kwargs)


def call_method(
    __name: MaybeEvaluatable[str], *args: Any, **kwargs: Any
) -> PipelineStep[Any, Any]:
    """Create a pipeline step that calls a method on the input.

    Arguments
    ---------
    __name : MaybeEvaluatable[str]
        The name of the method to call. This can be an Evaluatable that returns a string,
        or a constant string.
    *args : Any
        The positional arguments to pass to the method.
    **kwargs : Any
        The keyword arguments to pass to the method.

    Returns
    -------
    PipelineStep[Any, Any]
        A pipeline step that calls the method on the input.


    Example Usage
    -------------
    >>> from labrea import Option
    >>> import labrea.functions as F
    >>>
    >>> (Option('A') >> F.call_method('upper'))({'A': 'hello'})
    'HELLO'
    """
    return PipelineStep(
        partial(_call_method, __name, args, kwargs),
        f"call_method({__name!r}, {args!r}, {kwargs!r})",
    )
