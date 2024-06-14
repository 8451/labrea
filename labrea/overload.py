import threading
from typing import Callable, Dict, Hashable, Iterable, Optional, ParamSpec, Set, TypeVar

from .application import FunctionApplication
from .conditional import switch
from .evaluatable import Evaluatable
from .types import Options

A = TypeVar("A", covariant=True)
P = ParamSpec("P")


class Overloaded(Evaluatable[A]):
    """A class representing multiple implementations of an evaluatable."""

    dispatch: Evaluatable[Hashable]
    lookup: Dict[Hashable, Evaluatable[A]]
    switch: Evaluatable[A]
    _lock: threading.Lock

    def __init__(
        self, dispatch: Evaluatable[Hashable], lookup: Dict[Hashable, Evaluatable[A]]
    ):
        self.dispatch = dispatch
        self.lookup = lookup
        self.switch = switch(dispatch, lookup)
        self._lock = threading.Lock()

    def evaluate(self, options: Options) -> A:
        return self.switch.evaluate(options)

    def validate(self, options: Options) -> None:
        self.switch.validate(options)

    def keys(self, options: Options) -> Set[str]:
        return self.switch.keys(options)

    def __repr__(self) -> str:
        return f"Overloaded({self.dispatch!r}, {self.lookup!r})"

    def register(self, key: Hashable, value: Evaluatable[A]) -> None:
        with self._lock:
            self.lookup = {**self.lookup, key: value}
            self.switch = switch(self.dispatch, self.lookup)

    def overload(
        self,
        alias: Optional[Hashable] = None,
        aliases: Optional[Iterable[Hashable]] = None,
    ) -> Callable[[Callable[P, A]], FunctionApplication[P, A]]:
        aliases = aliases or []
        if alias is not None:
            aliases = [alias, *aliases]

        if not aliases:
            raise ValueError("At least one alias must be provided")

        def decorator(func: Callable[P, A]) -> FunctionApplication[P, A]:
            overload = FunctionApplication.lift(func)
            for key in aliases:
                self.register(key, overload)

            return overload

        return decorator
