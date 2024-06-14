from typing import Any, List, Optional, Set, TypeVar

from .evaluatable import Evaluatable, EvaluationError, MaybeEvaluatable
from .types import Options

A = TypeVar("A", covariant=True)


class CoalesceError(EvaluationError):
    """An error raised when no Evaluatable in a Coalesce can be evaluated"""

    def __init__(self, source: Evaluatable):
        super().__init__("No members of Coalesce returned a result", source)


class Coalesce(Evaluatable[A]):
    """Return the first Evaluatable that can be evaluated

    Takes 1 or more Evaluatables as arguments. Evaluates each Evaluatable in
    order until one can be evaluated. If none can be evaluated, raises an
    EvaluationError.
    """

    members: List[Evaluatable[A]]

    def __init__(self, __first: MaybeEvaluatable[A], *__rest: MaybeEvaluatable[A]):
        """Create a new Coalesce Evaluatable

        Parameters
        ----------
        __first : MaybeEvaluatable[A]
            The first Evaluatable to try to evaluate.
        *__rest : MaybeEvaluatable[A]
            The rest of the Evaluatables to try to evaluate.
        """
        self.members = [Evaluatable.ensure(arg) for arg in (__first, *__rest)]

    def evaluate(self, options: Options) -> A:
        """Evaluate the first Evaluatable that can be evaluated"""
        return self._delegate("evaluate", options)

    def validate(self, options: Options) -> None:
        """Determines if any of the Evaluatables can be validated."""
        return self._delegate("validate", options)

    def keys(self, options: Options) -> Set[str]:
        """Return the keys for the first Evaluatable that can be evaluated."""
        return self._delegate("keys", options)

    def _delegate(self, method: str, options: Options) -> Any:
        """Delegate a method to the first Evaluatable that can be evaluated."""
        err: Optional[EvaluationError] = None

        for member in self.members:
            try:
                return getattr(member, method)(options)
            except EvaluationError as e:
                err = e

        raise CoalesceError(self) from err

    def __repr__(self) -> str:
        return f"Coalesce({', '.join(map(repr, self.members))})"


coalesce = Coalesce
