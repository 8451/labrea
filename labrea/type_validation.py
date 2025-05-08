import warnings
from typing import Any, Mapping, Type

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


def _labrea_type_validation_handler(request: TypeValidationRequest):
    try:
        import labrea_type_validation
    except ImportError:
        warnings.warn(
            "labrea_type_validation is not installed; type validation will not be enforced"
        )
        return

    with labrea_type_validation.enabled():
        return request.run()


@TypeValidationRequest.handle
def _default_handler(request: TypeValidationRequest):
    # Have to manually inspect options here to avoid infinite loop
    labrea_opts = request.options.get("LABREA", {})
    if not isinstance(labrea_opts, Mapping):
        return

    type_validation_opts = labrea_opts.get("TYPE_VALIDATION", {})
    if not isinstance(type_validation_opts, Mapping):
        return

    if type_validation_opts.get("ENABLED", False) is not True:
        return

    return _labrea_type_validation_handler(request)
