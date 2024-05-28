from typing import Any

from .types import Alias, MultiAlias


def default_alias(obj: Any) -> Alias:
    try:
        name = obj.__name__
    except AttributeError:
        raise TypeError(
            f"A default alias for {obj} could not be created, please provide "
            f"one manually."
        )

    module = getattr(obj, "__module__", None)

    return name if module in ("__main__", None) else f"{module}.{name}"


def default_aliases(obj: Any) -> MultiAlias:
    return [default_alias(obj)]
