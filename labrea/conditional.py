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
from .evaluatable import (
    Evaluatable,
    EvaluationError,
    InsufficientInformationError,
    MaybeEvaluatable,
)
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


class Switch(Generic[K, V], Evaluatable[V]):
    """A class representing a switch statement."""

    dispatch: Evaluatable[K]
    lookup: Mapping[K, MaybeEvaluatable[V]]
    default: MaybeMissing[Evaluatable[V]]

    def __init__(
        self,
        dispatch: MaybeEvaluatable[K],
        lookup: Mapping[K, MaybeEvaluatable[V]],
        default: MaybeMissing[MaybeEvaluatable[V]] = MISSING,
    ) -> None:
        self.dispatch = Evaluatable.ensure(dispatch)
        self.lookup = lookup
        self.default = (
            Evaluatable.ensure(default) if default is not MISSING else default
        )

    def _dispatch(self, options: Options) -> MaybeMissing[K]:
        value: MaybeMissing[K]
        try:
            value = self.dispatch.evaluate(options)
        except EvaluationError as e:
            if self.default is MISSING:
                raise e
            else:
                value = MISSING

        return value

    def _lookup(self, key: MaybeMissing[K]) -> Evaluatable[V]:
        if key not in self.lookup:
            if self.default is MISSING:
                raise SwitchError(self.dispatch, key, self.lookup)  # type: ignore [misc]
            return self.default

        return Evaluatable.ensure(self.lookup.get(key, self.default))  # type: ignore [arg-type]

    def evaluate(self, options: Options) -> V:
        key = self._dispatch(options)
        return self._lookup(key).evaluate(options)

    def validate(self, options: Options) -> None:
        key = self._dispatch(options)
        self._lookup(key).validate(options)

    def keys(self, options: Options) -> Set[str]:
        key = self._dispatch(options)
        return (
            self.dispatch.keys(options) if key in self.lookup else set()
        ) | self._lookup(key).keys(options)

    def explain(self, options: Optional[Options] = None) -> Set[str]:
        try:
            key = self._dispatch(options or {})
            value = self._lookup(key)
        except EvaluationError as e:
            raise InsufficientInformationError(
                f"Could not evaluate {self.dispatch}", self
            ) from e

        return (
            self.dispatch.explain(options) if key in self.lookup else set()
        ) | value.explain(options)

    def __repr__(self) -> str:
        if self.default is MISSING:
            return f"switch({self.dispatch!r}, {self.lookup!r})"

        return f"switch({self.dispatch!r}, {self.lookup!r}, {self.default!r})"


switch = Switch


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
