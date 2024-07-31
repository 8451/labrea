from typing import Any, List, Optional, Set, TypeVar

from .exceptions import EvaluationError
from .types import Evaluatable, Options

A = TypeVar("A", covariant=True)


class Coalesce(Evaluatable[A]):
    """Return the first Evaluatable that can be evaluated

    Takes 1 or more Evaluatables as arguments. Evaluates each Evaluatable in
    order until one can be evaluated. If none can be evaluated, raises an
    EvaluationError.

    Aliases: :func:`labrea.coalesce`, :class:`labrea.Coalesce`


    Arguments
    ---------
    *evaluatables : MaybeEvaluatable[A]
        The evaluatables to evaluate.


    Example Usage
    -------------
    >>> from labrea import Coalesce, Option
    >>> c = Coalesce(Option('A.X'), Option('B.Y'))
    >>> c({'A': {'X': 1}, 'B': {'Y': 2}})
    1
    >>> c({'B': {'Y': 2}})
    2
    """

    members: List[Evaluatable[A]]

    def __init__(self, __first: Evaluatable[A], *__rest: Evaluatable[A]):
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
