import builtins
from typing import Dict, Hashable, TypeVar, Union

from .evaluatable import Evaluatable, MaybeEvaluatable

H = TypeVar("H", bound=Hashable)
B = TypeVar("B")


class SwitchError(Exception):
    """An error raised when a switch statement encounters an invalid value."""

    def __init__(
        self,
        evaluatable: Evaluatable[H],
        value: H,
        lookup: Dict[H, MaybeEvaluatable[B]],
    ):
        super().__init__(
            f"{evaluatable} evaluated to {value}, "
            f"but must be one of {', '.join(map(str, lookup.keys()))}."
        )


def switch(
    evaluatable: Evaluatable[H],
    lookup: Dict[H, MaybeEvaluatable[B]],
    default: Union[MaybeEvaluatable[B], builtins.ellipsis] = ...,
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
    default : Union[MaybeEvaluatable[B], ...], optional
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
        result: Union[MaybeEvaluatable[B], builtins.ellipsis] = lookup.get(
            value, default
        )

        if result is ...:
            raise SwitchError(evaluatable, value, lookup)

        return Evaluatable.ensure(result)

    return evaluatable.bind(_switch)
