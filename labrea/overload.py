import sys

if sys.version_info < (3, 10):
    from typing_extensions import ParamSpec
else:
    from typing import ParamSpec

import threading
from typing import Dict, Hashable, Optional, Set, TypeVar

from ._missing import MISSING, MaybeMissing
from .conditional import switch
from .types import Evaluatable, MaybeEvaluatable, Options

A = TypeVar("A", covariant=True)
P = ParamSpec("P")


class Overloaded(Evaluatable[A]):
    """A class representing multiple implementations of an Evaluatable.

    This class generalizes the idea of dataset overloads. It takes a dispatch,
    which is an evaluatable (like an Option) that returns a key, and a lookup
    dictionary, which maps keys to evaluatables. When the overloaded object is
    evaluated, it uses the dispatch to determine which evaluatable to use, and
    then evaluates that evaluatable. An optional default evaluatable can be
    provided, which is used if the dispatch key is not found in the lookup
    dictionary, or if the dispatch cannot be evaluated.

    Arguments
    ----------
    dispatch : Evaluatable[Hashable]
        The evaluatable that determines which implementation to use.
    lookup : Dict[Hashable, Evaluatable[A]], optional
        A dictionary mapping keys to evaluatables.
    default : MaybeMissing[MaybeEvaluatable[A]], optional
        The default evaluatable to use if the dispatch key is not found in the
        lookup dictionary. If this is not provided, an exception will be raised
        if the dispatch key is not found.
    """

    dispatch: Evaluatable[Hashable]
    lookup: Dict[Hashable, Evaluatable[A]]
    default: MaybeMissing[Evaluatable[A]]
    _lock: threading.Lock

    def __init__(
        self,
        dispatch: Evaluatable[Hashable],
        lookup: Optional[Dict[Hashable, Evaluatable[A]]],
        default: MaybeMissing[MaybeEvaluatable[A]] = MISSING,
    ):
        self.dispatch = dispatch
        self.lookup = lookup or {}
        self.default = (
            Evaluatable.ensure(default) if default is not MISSING else default
        )
        self._lock = threading.Lock()

    def evaluate(self, options: Options) -> A:
        """Evaluate the dispatch, and then evaluate the selected implementation."""
        return self.switch.evaluate(options)

    def validate(self, options: Options) -> None:
        """Validate the dispatch and the selected implementation."""
        self.switch.validate(options)

    def keys(self, options: Options) -> Set[str]:
        """Return the option keys required by the dispatch and the selected implementation.""" ""
        return self.switch.keys(options)

    def explain(self, options: Optional[Options] = None) -> Set[str]:
        """Return the option keys required by the dispatch and the selected implementation."""
        return self.switch.explain(options)

    def __repr__(self) -> str:
        if self.default is MISSING:
            return f"Overloaded({self.dispatch!r}, {self.lookup!r})"

        return f"Overloaded({self.dispatch!r}, {self.lookup!r}, {self.default!r})"

    def register(self, key: Hashable, value: Evaluatable[A]) -> None:
        """Register a new implementation with the overloaded object.

        Arguments
        ----------
        key : Hashable
            The key for the implementation.
        value : Evaluatable[A]
            The implementation to register.
        """
        with self._lock:
            self.lookup = {**self.lookup, key: value}

    @property
    def switch(self) -> Evaluatable[A]:
        """Return the switch evaluatable that determines which implementation to use."""
        return switch(self.dispatch, self.lookup, default=self.default)
