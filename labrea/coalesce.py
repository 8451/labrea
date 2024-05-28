from typing import List, Set, TypeVar, Union

from .types import Evaluatable, EvaluationError, JSONDict, ValidationError, Value

A = TypeVar("A")


class Coalesce(Evaluatable[A]):
    """Return the first Evaluatable that can be evaluated

    Takes 1 or more Evaluatables as arguments. Evaluates each Evaluatable in
    order until one can be evaluated. If none can be evaluated, raises an
    EvaluationError.
    """

    members: List[Evaluatable[A]]

    def __init__(self, __first, *__rest: Union[A, Evaluatable[A]]):
        """Create a new Coalesce Evaluatable

        Parameters
        ----------
        __first : Union[A, Evaluatable[A]]
            The first Evaluatable to try to evaluate.
        *__rest : Union[A, Evaluatable[A]]
            The rest of the Evaluatables to try to evaluate.
        """
        self.members = [
            arg if isinstance(arg, Evaluatable) else Value(arg)
            for arg in (__first, *__rest)
        ]

    def evaluate(self, options: JSONDict) -> A:
        """Evaluate the first Evaluatable that can be evaluated

        See Also
        --------
        labrea.types.Evaluatable.evaluate
        """
        for member in self.members:
            try:
                member.validate(options)
                return member.evaluate(options)
            except (ValidationError, EvaluationError):
                continue

        raise EvaluationError("No members of Coalesce returned a result")

    def validate(self, options: JSONDict) -> None:
        """Attempt to validate each Evaluatable in order

        If none can be validated, raises a ValidationError.

        See Also
        --------
        labrea.types.Validatable.validate
        """
        for member in self.members:
            try:
                member.validate(options)
                return
            except ValidationError:
                continue

        self.members[0].validate(options)

    def keys(self, options: JSONDict) -> Set[str]:
        """Return the keys for the first Evaluatable that can be validated

        If none can be validated, returns an empty set.

        See Also
        --------
        labrea.types.Validatable.keys
        """
        for member in self.members:
            try:
                member.validate(options)
                return member.keys(options)
            except ValidationError:
                continue

        return set()
