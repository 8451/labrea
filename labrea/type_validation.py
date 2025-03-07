from typing import Any, Type

from ._missing import MISSING, MaybeMissing
from .exceptions import EvaluationError
from .runtime import Request
from .types import Evaluatable, Options


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


class TypeValidationRequest(Request[None]):
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
    type: MaybeMissing[Type]
    options: Options

    def __init__(self, value: Any, type: MaybeMissing[Type], options: Options):
        self.value = value
        self.type = type
        self.options = options


@TypeValidationRequest.handle
def _empty_handler(request: TypeValidationRequest):
    return


def validate(
    source: Evaluatable, value: Any, type: MaybeMissing[Type], options: Options
) -> None:
    if type is MISSING:
        return
    try:
        TypeValidationRequest(value, type, options).run()
    except TypeError as e:
        raise TypeValidationError(source, value, type) from e
