from typing import Any, List, Optional, Set, TypeVar

from .exceptions import EvaluationError
from .types import Evaluatable, MaybeEvaluatable, Options

A = TypeVar("A", covariant=True)


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

    def explain(self, options: Optional[Options] = None) -> Set[str]:
        """Return the explanation for the first Evaluatable that can be evaluated."""
        try:
            return self._delegate("explain", options)
        except EvaluationError:
            return self.members[-1].explain(options)

    def _delegate(self, method: str, options: Optional[Options] = None) -> Any:
        """Delegate a method to the first Evaluatable that can be evaluated."""
        options = options or {}
        err: Optional[EvaluationError] = None

        for member in self.members:
            try:
                member.validate(options)
                return getattr(member, method)(options)
            except EvaluationError as e:
                err = e

        raise err  # type: ignore

    def __repr__(self) -> str:
        return f"Coalesce({', '.join(map(repr, self.members))})"


coalesce = Coalesce
