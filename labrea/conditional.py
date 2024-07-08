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
    Union,
)

from ._missing import MISSING, MaybeMissing
from .exceptions import EvaluationError, InsufficientInformationError
from .option import Option
from .types import Evaluatable, MaybeEvaluatable, Options

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


class _DependsOn(Generic[A, B], Evaluatable[B]):
    evaluatable: Evaluatable[B]
    depends: Evaluatable[A]

    def __init__(
        self, evaluatable: MaybeEvaluatable[B], depends: MaybeEvaluatable[A]
    ) -> None:
        self.evaluatable = Evaluatable.ensure(evaluatable)
        self.depends = Evaluatable.ensure(depends)

    def evaluate(self, options: Options) -> B:
        return self.evaluatable.evaluate(options)

    def validate(self, options: Options) -> None:
        self.evaluatable.validate(options)

    def keys(self, options: Options) -> Set[str]:
        return self.evaluatable.keys(options) | self.depends.keys(options)

    def explain(self, options: Optional[Options] = None) -> Set[str]:
        return self.evaluatable.explain(options) | self.depends.explain(options)

    def __repr__(self) -> str:
        return f"_DependsOn({self.evaluatable!r}, {self.depends!r})"  # pragma: no cover


class Switch(Generic[K, V], Evaluatable[V]):
    dispatch: Evaluatable[K]
    lookup: Mapping[K, Evaluatable[V]]
    default: MaybeMissing[Evaluatable[V]]

    def __init__(
        self,
        dispatch: Union[str, Evaluatable[K]],
        lookup: Mapping[K, MaybeEvaluatable[V]],
        default: MaybeMissing[MaybeEvaluatable[V]] = MISSING,
    ) -> None:
        self.dispatch = (
            dispatch if isinstance(dispatch, Evaluatable) else Option(dispatch)
        )
        self.lookup = {key: Evaluatable.ensure(value) for key, value in lookup.items()}
        self.default = (
            Evaluatable.ensure(default) if default is not MISSING else default
        )

    def _dispatch(self, options: Options) -> K:
        return self.dispatch.evaluate(options)

    def _lookup(self, options: Options) -> Evaluatable[V]:
        try:
            key = self._dispatch(options)
        except EvaluationError as e:
            if self.default is MISSING:
                raise e
            return self.default

        if key not in self.lookup:
            if self.default is MISSING:
                raise SwitchError(self.dispatch, key, self.lookup)  # type: ignore  [arg-type]
            return self.default

        return _DependsOn(self.lookup[key], self.dispatch)  # type: ignore  [arg-type]

    def evaluate(self, options: Options) -> V:
        return self._lookup(options).evaluate(options)

    def validate(self, options: Options) -> None:
        self._lookup(options).validate(options)

    def keys(self, options: Options) -> Set[str]:
        return self._lookup(options).keys(options)

    def explain(self, options: Optional[Options] = None) -> Set[str]:
        options = options or {}
        try:
            chosen = self._lookup(options)
        except EvaluationError as e:
            raise InsufficientInformationError(
                "Could not determine the switch branch", self
            ) from e

        return chosen.explain(options)

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
