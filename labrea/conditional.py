import sys

if sys.version_info < (3, 11):
    from typing import NoReturn as Never
else:
    from typing import Never

import functools
from typing import (
    Any,
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
    overload,
)

from ._missing import MISSING, MaybeMissing
from .exceptions import EvaluationError, InsufficientInformationError
from .option import Option
from .types import Evaluatable, MaybeEvaluatable, Options

A = TypeVar("A")
B = TypeVar("B")
C = TypeVar("C")
V = TypeVar("V")


class SwitchError(EvaluationError):
    """An error raised when a switch statement encounters an invalid key."""

    def __init__(
        self,
        dispatch: Evaluatable[Hashable],
        value: Hashable,
        lookup: Mapping[Hashable, Any],
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


class Switch(Evaluatable[V]):
    """A class representing a switch statement.

    This class takes a dispatch evaluatable and a mapping of keys to evaluatables.
    When evaluated, the dispatch is evaluated and the corresponding value is
    evaluated and returned. If the key is not found in the mapping, or the dispatch
    cannot be evaluated, a default value can be provided. If no default is provided,
    and the switch cannot choose a branch, an error is raised.

    Aliases: :func:`labrea.switch`, :class:`labrea.Switch`


    Arguments
    ---------
    dispatch : Union[str, Evaluatable[Hashable]]
        The dispatch evaluatable. This is used to determine which branch to take.
    lookup : Mapping[Hashable, MaybeEvaluatable[V]]
        A mapping of keys to evaluatables. The key is determined by the dispatch.
        Values can also be plain values.
    default : MaybeMissing[MaybeEvaluatable[V]], optional
        The default value to use if the key is not found in the mapping. Can be
        an evaluatable, or a plain value.


    Example Usage
    -------------
    >>> from labrea import Option, switch
    >>> s = switch(Option('A'), {True: Option('X'), False: Option('Y')}, Option('Z'))
    >>> s({'A': True, 'X': 'Hello', 'Y': 'World', 'Z': 'Default'})
    'Hello'
    >>> s({'A': False, 'X': 'Hello', 'Y': 'World', 'Z': 'Default'})
    'World'
    >>> s({'A': None, 'X': 'Hello', 'Y': 'World', 'Z': 'Default'})
    'Default'
    >>> s({'X': 'Hello', 'Y': 'World', 'Z': 'Default'})
    'Default'
    """

    dispatch: Evaluatable[Hashable]
    lookup: Mapping[Hashable, Evaluatable[V]]
    default: MaybeMissing[Evaluatable[V]]

    def __init__(
        self,
        dispatch: Union[str, Evaluatable[Hashable]],
        lookup: Mapping[Hashable, Evaluatable[V]],
        default: MaybeMissing[MaybeEvaluatable[V]] = MISSING,
    ) -> None:
        self.dispatch = (
            dispatch if isinstance(dispatch, Evaluatable) else Option(dispatch)
        )
        self.lookup = {key: Evaluatable.ensure(value) for key, value in lookup.items()}
        self.default = (
            Evaluatable.ensure(default) if default is not MISSING else default
        )

    def _dispatch(self, options: Options) -> Hashable:
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
        """Evaluate the switch statement and return the result."""
        return self._lookup(options).evaluate(options)

    def validate(self, options: Options) -> None:
        """Validate that the switch statement can be evaluated."""
        self._lookup(options).validate(options)

    def keys(self, options: Options) -> Set[str]:
        """Return the option keys required by the switch statement."""
        return self._lookup(options).keys(options)

    def explain(self, options: Optional[Options] = None) -> Set[str]:
        """Return the option keys required by the switch statement."""
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
    """A class representing a case when statement.

    This class takes a dispatch evaluatable and a sequence of cases. Each case is
    a condition and a result. When evaluated, the dispatch is evaluated and the
    corresponding case is matched. If no case is matched, a default value can be
    provided. If no default is provided, and the case cannot choose a branch, an
    error is raised.

    This class is not usually instantiated directly. Instead, use the :code:`case` function.
    """

    dispatch: Evaluatable[A]
    cases: Sequence[Tuple[Evaluatable[Callable[[A], bool]], Evaluatable[B]]]
    default: MaybeMissing[Evaluatable[B]]

    def __init__(
        self,
        dispatch: Evaluatable[A],
        cases: Sequence[Tuple[Evaluatable[Callable[[A], bool]], Evaluatable[B]]],
        default: MaybeMissing[Evaluatable[B]] = MISSING,
    ) -> None:
        self.dispatch = dispatch
        self.cases = [(condition, result) for condition, result in cases]
        self.default = default

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
        """Evaluate the case when statement and return the result."""
        return self._bound(options).evaluate(options)

    def validate(self, options: Options) -> None:
        """Validate that the case when statement can be evaluated."""
        self._bound(options).validate(options)

    def keys(self, options: Options) -> Set[str]:
        """Return the option keys required by the case when statement."""
        return self._bound(options).keys(options)

    def explain(self, options: Optional[Options] = None) -> Set[str]:
        """Return the option keys required by the case when statement."""
        return self._bound(options or {}).explain(options)

    @overload
    def when(
        self,
        condition: MaybeEvaluatable[Callable[[A], bool]],
        result: Evaluatable[C],
    ) -> "CaseWhen[A, Union[B, C]]":
        ...

    @overload
    def when(
        self,
        condition: MaybeEvaluatable[Callable[[A], bool]],
        result: C,
    ) -> "CaseWhen[A, Union[B, C]]":
        ...

    def when(
        self,
        condition: MaybeEvaluatable[Callable[[A], bool]],
        result: MaybeEvaluatable[C],
    ) -> "CaseWhen[A, Union[B, C]]":
        """Add a case to the case when statement. Returns a new instance.

        Arguments
        ---------
        condition : Union[str, Callable[[A], bool]]
            The condition to match. Can be a plain value or a callable.
        result : MaybeEvaluatable[B]
            The result to return if the condition is matched.
        """
        return CaseWhen(
            self.dispatch,
            [*self.cases, (Evaluatable.ensure(condition), Evaluatable.ensure(result))],
            self.default,
        )

    @overload
    def otherwise(self, default: Evaluatable[C]) -> "CaseWhen[A, Union[B, C]]":
        ...

    @overload
    def otherwise(self, default: C) -> "CaseWhen[A, Union[B, C]]":
        ...

    def otherwise(self, default: MaybeEvaluatable[C]) -> "CaseWhen[A, Union[B, C]]":
        """Add a default value to the case when statement. Returns a new instance.

        Arguments
        ---------
        default : MaybeEvaluatable[B]
            The default value to return if no case is matched.
        """
        return CaseWhen(self.dispatch, self.cases, Evaluatable.ensure(default))

    def __repr__(self) -> str:
        _base = f"case({self.dispatch!r})"
        _cases = ", ".join(
            f"when({condition!r}, {result!r})" for condition, result in self.cases
        )
        _default = (
            f".otherwise({self.default!r})" if self.default is not MISSING else ""
        )
        return f"{_base}.{_cases}{_default}"


@overload
def case(dispatch: Evaluatable[A]) -> CaseWhen[A, Never]:
    ...


@overload
def case(dispatch: A) -> CaseWhen[A, Never]:
    ...


def case(dispatch: MaybeEvaluatable[A]) -> CaseWhen[A, Never]:
    """Create a case when statement.

    This is the preferred method for creating a case when statement.
    It allows for chaining multiple cases and a default value.

    Arguments
    ---------
    dispatch : MaybeEvaluatable[A]
        The dispatch evaluatable. This is used to determine which branch to take.

    Returns
    -------
    CaseWhen[A, B]
        A new case when statement with no cases or default.


    Example Usage
    -------------
    >>> from labrea import Option, case
    >>> c = case(
    ...     Option('A')
    ... ).when(
    ...     lambda a: a < 0,
    ...     Option('X')
    ... ).when(
    ...     lambda a: a > 0,
    ...     Option('Y')
    ... ).otherwise(Option('Z'))
    >>> c({'A': -1, 'X': 'Negative', 'Y': 'Positive', 'Z': 'Zero'})
    'Negative'
    >>> c({'A': 1, 'X': 'Negative', 'Y': 'Positive', 'Z': 'Zero'})
    'Positive'
    >>> c({'A': 0, 'X': 'Negative', 'Y': 'Positive', 'Z': 'Zero'})
    'Zero'
    """
    return CaseWhen(Evaluatable.ensure(dispatch), [])
