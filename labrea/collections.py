from typing import Dict, Hashable, List, Set, Tuple, TypeVar, Union, overload

from .iterable import Iter
from .types import Evaluatable, Value

A = TypeVar("A")
K = TypeVar("K", bound=Hashable)
V = TypeVar("V")
T1 = TypeVar("T1")
T2 = TypeVar("T2")
T3 = TypeVar("T3")
T4 = TypeVar("T4")
T5 = TypeVar("T5")
T6 = TypeVar("T6")
T7 = TypeVar("T7")
T8 = TypeVar("T8")


def evaluatable_list(*evaluatables: Evaluatable[A]) -> Evaluatable[List[A]]:
    """Create an Evaluatable that evaluates to a list of values.

    This function is a convenience wrapper around Iter.apply(list).

    Aliases: :func:`labrea.DatasetList`, :func:`labrea.evaluatable_list`

    Arguments
    ---------
    *evaluatables : Evaluatable[A]
        The objects to evaluate.
    """
    return Iter(*evaluatables).apply(list)


@overload
def evaluatable_tuple(
    __e1: Evaluatable[T1],
) -> Evaluatable[Tuple[T1]]:
    ...


@overload
def evaluatable_tuple(
    __e1: Evaluatable[T1],
    __e2: Evaluatable[T2],
) -> Evaluatable[Tuple[T1, T2]]:
    ...


@overload
def evaluatable_tuple(
    __e1: Evaluatable[T1],
    __e2: Evaluatable[T2],
    __e3: Evaluatable[T3],
) -> Evaluatable[Tuple[T1, T2, T3]]:
    ...


@overload
def evaluatable_tuple(
    __e1: Evaluatable[T1],
    __e2: Evaluatable[T2],
    __e3: Evaluatable[T3],
    __e4: Evaluatable[T4],
) -> Evaluatable[Tuple[T1, T2, T3, T4]]:
    ...


@overload
def evaluatable_tuple(
    __e1: Evaluatable[T1],
    __e2: Evaluatable[T2],
    __e3: Evaluatable[T3],
    __e4: Evaluatable[T4],
    __e5: Evaluatable[T5],
) -> Evaluatable[Tuple[T1, T2, T3, T4, T5]]:
    ...


@overload
def evaluatable_tuple(
    __e1: Evaluatable[T1],
    __e2: Evaluatable[T2],
    __e3: Evaluatable[T3],
    __e4: Evaluatable[T4],
    __e5: Evaluatable[T5],
    __e6: Evaluatable[T6],
) -> Evaluatable[Tuple[T1, T2, T3, T4, T5, T6]]:
    ...


@overload
def evaluatable_tuple(
    __e1: Evaluatable[T1],
    __e2: Evaluatable[T2],
    __e3: Evaluatable[T3],
    __e4: Evaluatable[T4],
    __e5: Evaluatable[T5],
    __e6: Evaluatable[T6],
    __e7: Evaluatable[T7],
) -> Evaluatable[Tuple[T1, T2, T3, T4, T5, T6, T7]]:
    ...


@overload
def evaluatable_tuple(
    __e1: Evaluatable[T1],
    __e2: Evaluatable[T2],
    __e3: Evaluatable[T3],
    __e4: Evaluatable[T4],
    __e5: Evaluatable[T5],
    __e6: Evaluatable[T6],
    __e7: Evaluatable[T7],
    __e8: Evaluatable[T8],
) -> Evaluatable[Tuple[T1, T2, T3, T4, T5, T6, T7, T8]]:
    ...


def evaluatable_tuple(*evaluatables: Evaluatable[A]) -> Evaluatable[Tuple[A, ...]]:
    """Create an Evaluatable that evaluates to a tuple of values.

    This function is a convenience wrapper around Iter.apply(tuple).

    Aliases: :func:`labrea.DatasetTuple`, :func:`labrea.evaluatable_tuple`

    Arguments
    ---------
    *evaluatables : Evaluatable[A]
        The objects to evaluate.
    """
    return Iter(*evaluatables).apply(tuple)


def evaluatable_set(*evaluatables: Evaluatable[K]) -> Evaluatable[Set[K]]:
    """Create an Evaluatable that evaluates to a set of values.

    This function is a convenience wrapper around Iter.apply(set).

    Aliases: :func:`labrea.DatasetSet`, :func:`labrea.evaluatable_set`

    Arguments
    ---------
    *evaluatables : Evaluatable[K]
        The objects to evaluate.
    """
    return Iter(*evaluatables).apply(set)


def evaluatable_dict(contents: Dict[K, Evaluatable[V]]) -> Evaluatable[Dict[K, V]]:
    """Create an Evaluatable that evaluates to a dictionary of values.

    This function is a convenience wrapper around Iter.apply(dict).

    Aliases: :func:`labrea.DatasetDict`, :func:`labrea.evaluatable_dict`

    Arguments
    ---------
    contents : Dict[K, Evaluatable[V]]
        The objects to evaluate.
    """
    pairs = (Iter[Union[K, V]](Value(key), val) for key, val in contents.items())
    return Iter(*pairs).apply(dict)  # type: ignore


DatasetList = evaluatable_list
DatasetTuple = evaluatable_tuple
DatasetSet = evaluatable_set
DatasetDict = evaluatable_dict
