import functools
from typing import (
    Callable,
    Generic,
    Hashable,
    Mapping,
    Optional,
    Sequence,
    Set,
    Tuple,
    TypeVar,
)

from ._missing import MISSING, MaybeMissing
from .coalesce import coalesce
from .evaluatable import Evaluatable, EvaluationError, MaybeEvaluatable
from .types import Options

A = TypeVar("A")
B = TypeVar("B")
K = TypeVar("K", bound=Hashable)
V = TypeVar("V")


class SwitchError(EvaluationError):
    """An error raised when a switch statement encounters an invalid key."""

    def __init__(
        self,
        dispatch: Evaluatable[K],
        value: K,
        lookup: Mapping[K, MaybeEvaluatable[V]],
    ):
        super().__init__(
            f"Evaluated to {value}, "
            f"but must be one of {', '.join(map(str, lookup.keys()))}.",
            dispatch,
        )


def switch(
    dispatch: Evaluatable[K],
    lookup: Mapping[K, MaybeEvaluatable[V]],
    default: MaybeMissing[MaybeEvaluatable[V]] = MISSING,
) -> Evaluatable[V]:
    def _switch(key: K) -> Evaluatable[V]:
        if key not in lookup:
            raise SwitchError(dispatch, key, lookup)

        return Evaluatable.ensure(lookup[key])

    return (
        dispatch.bind(_switch)
        if default is MISSING
        else coalesce(dispatch.bind(_switch), default)
    )


Switch = switch


class CaseWhenError(EvaluationError):
    """An error raised when a case when statement encounters an invalid key."""

    def __init__(self, dispatch: Evaluatable[A], value: A):
        super().__init__(
            f"Evaluated to {value}, which does not match any of the cases, "
            f"and no default was provided.",
            dispatch,
        )


class CaseWhen(Generic[A, B], Evaluatable[B]):
    """A class representing a case when statement."""

    dispatch: Evaluatable[A]
    cases: Sequence[Tuple[Evaluatable[Callable[[A], bool]], Evaluatable[B]]]
    default: MaybeMissing[Evaluatable[B]]

    def __init__(
        self,
        dispatch: MaybeEvaluatable[A],
        cases: Sequence[
            Tuple[MaybeEvaluatable[Callable[[A], bool]], MaybeEvaluatable[B]]
        ],
        default: MaybeMissing[MaybeEvaluatable[B]] = MISSING,
    ) -> None:
        self.dispatch = Evaluatable.ensure(dispatch)
        self.cases = [
            (Evaluatable.ensure(condition), Evaluatable.ensure(result))
            for condition, result in cases
        ]
        self.default = (
            Evaluatable.ensure(default) if default is not MISSING else default
        )

    def _evaluate(self, value: A, options: Options) -> Evaluatable[B]:
        for condition, result in self.cases:
            if condition.evaluate(options)(value):
                return result

        if self.default is not MISSING:
            return self.default

        raise CaseWhenError(self.dispatch, value)

    def _bound(self, options: Options) -> Evaluatable[B]:
        return self.dispatch.bind(functools.partial(self._evaluate, options=options))

    def evaluate(self, options: Options) -> B:
        return self._bound(options).evaluate(options)

    def validate(self, options: Options) -> None:
        self._bound(options).validate(options)

    def keys(self, options: Options) -> Set[str]:
        return self._bound(options).keys(options)

    def explain(self, options: Optional[Options] = None) -> Set[str]:
        return self._bound(options or {}).explain(options)

    def when(
        self,
        condition: MaybeEvaluatable[Callable[[A], bool]],
        result: MaybeEvaluatable[B],
    ) -> "CaseWhen[A, B]":
        return CaseWhen(self.dispatch, [*self.cases, (condition, result)], self.default)

    def otherwise(self, default: MaybeEvaluatable[B]) -> "CaseWhen[A, B]":
        return CaseWhen(self.dispatch, self.cases, default)

    def __repr__(self) -> str:
        _base = f"case({self.dispatch!r})"
        _cases = ", ".join(
            f"when({condition!r}, {result!r})" for condition, result in self.cases
        )
        _default = (
            f".otherwise({self.default!r})" if self.default is not MISSING else ""
        )
        return f"{_base}.{_cases}{_default}"


def case(dispatch: MaybeEvaluatable[A]) -> CaseWhen[A, B]:
    return CaseWhen(dispatch, [])
