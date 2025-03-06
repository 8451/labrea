import warnings
from typing import Any, TypeVar

import pydantic

from ._missing import MISSING

PYDANTIC_MAJOR_VERSION = pydantic.version.VERSION.split(".")[0]
INVALID_PYDANTIC_VERSION = PYDANTIC_MAJOR_VERSION in frozenset({"0", "1"})

if INVALID_PYDANTIC_VERSION:
    warnings.warn(
        "The version of Pydantic installed is not supported. "
        "Please upgrade to Pydantic 2.0.0 or later.",
    )


A = TypeVar("A")


def validate(value: A, type: Any) -> A:
    if type is MISSING or INVALID_PYDANTIC_VERSION:
        return value

    return pydantic.TypeAdapter(type).validate_python(value, strict=True)
