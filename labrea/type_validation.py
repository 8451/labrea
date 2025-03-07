from typing import Any, Type, TypeVar

from ._missing import MaybeMissing
from .exceptions import EvaluationError
from .runtime import Request
from .types import Evaluatable, Options

A = TypeVar("A")


class TypeValidationError(EvaluationError):
    source: Evaluatable
    value: Any
    type: Type

    def __init__(self, source: Evaluatable, value: Any, type: Type) -> None:
        self.source = source
        self.value = value
        self.type = type

        super().__init__(
            f"Type validation failed for {source!r}: {value!r} is not of type {type!r}",
            source,
        )


class TypeValidationRequest(Request[A]):
    """A request to validate a type.

    Arguments
    ---------
    value : Any
        The value to validate.
    type : MaybeMissing[Type[A]]
        The type to validate against.
    options : Options
        The options used during evaluation.
    """

    value: Any
    type: MaybeMissing[Type[A]]
    options: Options

    def __init__(self, value: Any, type: MaybeMissing[Type[A]], options: Options):
        self.value = value
        self.type = type
        self.options = options


@TypeValidationRequest.handle
def _empty_handler(request: TypeValidationRequest[A]) -> A:
    return request.value
