from typing import Hashable, Mapping, TypeVar

from ._missing import MISSING, MaybeMissing
from .evaluatable import Evaluatable, EvaluationError, MaybeEvaluatable

H = TypeVar("H", bound=Hashable)
B = TypeVar("B")


class SwitchError(EvaluationError):
    """An error raised when a switch statement encounters an invalid value."""

    def __init__(
        self,
        evaluatable: Evaluatable[H],
        value: H,
        lookup: Mapping[H, MaybeEvaluatable[B]],
    ):
        super().__init__(
            f"Evaluated to {value}, "
            f"but must be one of {', '.join(map(str, lookup.keys()))}.",
            evaluatable,
        )


def switch(
    evaluatable: Evaluatable[H],
    lookup: Mapping[H, MaybeEvaluatable[B]],
    default: MaybeMissing[MaybeEvaluatable[B]] = MISSING,
) -> Evaluatable[B]:
    """Evaluates the given evaluatable and returns the value associated with it in the lookup table.

    If the value is not found in the lookup table, the default value is returned.
    If a default value is not provided, a KeyError is raised.

    Arguments
    ----------
    evaluatable : Evaluatable[H]
        The evaluatable to evaluate.
    lookup : Dict[H, MaybeEvaluatable[B]]
        The lookup table.
    default : MaybeEvaluatable[B], optional
        The default value to return if the value is not found in the lookup table.

    Returns
    -------
    Evaluatable[B]
        The evaluatable that evaluates to the value associated with the evaluated value in the
        lookup table.

    Raises
    ------
    SwitchError
        If the value is not found in the lookup table and a default value is not provided.
    """

    def _switch(value: H) -> Evaluatable[B]:
        result: MaybeMissing[MaybeEvaluatable[B]] = lookup.get(value, default)

        if result is MISSING:
            raise SwitchError(evaluatable, value, lookup)

        return Evaluatable.ensure(result)

    return evaluatable.bind(_switch)


Switch = switch
