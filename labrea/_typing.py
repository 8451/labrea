from typing import Any, TypeVar

from ._missing import MISSING

A = TypeVar("A")


def validate(value: A, type: Any) -> A:
    if type is MISSING:
        return value
    try:
        import pydantic
    except ImportError:
        return value

    if pydantic.version.VERSION.split(".")[0] < "1":
        return value

    return pydantic.TypeAdapter(type).validate_python(value, strict=True)
