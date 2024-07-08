import sys

if sys.version_info < (3, 10):
    from typing_extensions import ParamSpec
else:
    from typing import ParamSpec

import threading
from typing import Callable, Dict, Hashable, List, Optional, Set, TypeVar, Union

from ._missing import MISSING, MaybeMissing
from .application import FunctionApplication
from .conditional import switch
from .types import Evaluatable, MaybeEvaluatable, Options

A = TypeVar("A", covariant=True)
P = ParamSpec("P")


class Overloaded(Evaluatable[A]):
    """A class representing multiple implementations of an Evaluatable."""

    dispatch: Evaluatable[Hashable]
    lookup: Dict[Hashable, Evaluatable[A]]
    default: MaybeMissing[Evaluatable[A]]
    _lock: threading.Lock

    def __init__(
        self,
        dispatch: Evaluatable[Hashable],
        lookup: Dict[Hashable, Evaluatable[A]],
        default: MaybeMissing[MaybeEvaluatable[A]] = MISSING,
    ):
        self.dispatch = dispatch
        self.lookup = lookup
        self.default = (
            Evaluatable.ensure(default) if default is not MISSING else default
        )
        self._lock = threading.Lock()

    def evaluate(self, options: Options) -> A:
        return self.switch.evaluate(options)

    def validate(self, options: Options) -> None:
        self.switch.validate(options)

    def keys(self, options: Options) -> Set[str]:
        return self.switch.keys(options)

    def explain(self, options: Optional[Options] = None) -> Set[str]:
        return self.switch.explain(options)

    def __repr__(self) -> str:
        if self.default is MISSING:
            return f"Overloaded({self.dispatch!r}, {self.lookup!r})"

        return f"Overloaded({self.dispatch!r}, {self.lookup!r}, {self.default!r})"

    def register(self, key: Hashable, value: Evaluatable[A]) -> None:
        with self._lock:
            self.lookup = {**self.lookup, key: value}

    @property
    def switch(self) -> Evaluatable[A]:
        return switch(self.dispatch, self.lookup, default=self.default)

    def overload(
        self,
        alias: Union[Hashable, List[Hashable]],
    ) -> Callable[[Callable[P, A]], FunctionApplication[P, A]]:
        aliases = alias if isinstance(alias, list) else [alias]

        def decorator(func: Callable[P, A]) -> FunctionApplication[P, A]:
            overload = FunctionApplication.lift(func)
            for key in aliases:
                self.register(key, overload)

            return overload

        return decorator


def overloaded(
    dispatch: Evaluatable[Hashable],
) -> Callable[[Evaluatable[A]], Overloaded[A]]:
    return lambda default: Overloaded(dispatch, {}, default)
