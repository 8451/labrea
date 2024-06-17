from typing import Dict, Hashable, List, Tuple, TypeVar, Union

from .evaluatable import Evaluatable, MaybeEvaluatable, Value
from .iterable import Iter

A = TypeVar("A")
K = TypeVar("K", bound=Hashable)
V = TypeVar("V")


def evaluatable_list(*evaluatables: MaybeEvaluatable[A]) -> Evaluatable[List[A]]:
    return Iter(*evaluatables).apply(list)


def evaluatable_tuple(*evaluatables: MaybeEvaluatable[A]) -> Evaluatable[Tuple[A, ...]]:
    return Iter(*evaluatables).apply(tuple)


def evaluatable_set(*evaluatables: MaybeEvaluatable[K]) -> Evaluatable[set[K]]:
    return Iter(*evaluatables).apply(set)


def evaluatable_dict(contents: Dict[K, MaybeEvaluatable[V]]) -> Evaluatable[Dict[K, V]]:
    pairs = (Iter[Union[K, V]](Value(key), val) for key, val in contents.items())
    return Iter(*pairs).apply(dict)  # type: ignore


DatasetList = evaluatable_list
DatasetTuple = evaluatable_tuple
DatasetSet = evaluatable_set
DatasetDict = evaluatable_dict
