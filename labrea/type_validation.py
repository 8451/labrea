from typing import Any, Type

from .runtime import Request
from .types import Options


class TypeValidationRequest(Request[None]):
    """A request to validate a type.

    Arguments
    ---------
    value : Any
        The value to validate.
    type : Type[A]
        The type to validate against.
    options : Options
        The options used during evaluation.
    """

    value: Any
    type: Type
    options: Options

    def __init__(self, value: Any, type: Type, options: Options):
        self.value = value
        self.type = type
        self.options = options


@TypeValidationRequest.handle
def _empty_handler(request: TypeValidationRequest):
    return
