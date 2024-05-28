from functools import reduce
from importlib import import_module
from types import ModuleType
from typing import Any, List, Tuple, TypeVar

A = TypeVar("A")


def _import_module(path: List[str]) -> Tuple[ModuleType, List[str]]:
    if len(path) == 0:
        raise ImportError

    try:
        return import_module(".".join(path)), []
    except ModuleNotFoundError:
        path, attrs = path[:-1], path[-1:]
        module, rest = _import_module(path)
        return module, rest + attrs


def _getattr(namespace: Any, name: str):
    try:
        return getattr(namespace, name)
    except AttributeError as err:
        raise ImportError(f'"{namespace}" does not define attribute "{name}"') from err


def import_string(dotted_path: str) -> Any:
    """
    Import a dotted module path and return the attribute/class designated by
    the last name in the path. Raise ImportError if the import failed.
    """
    module, attrs = _import_module(dotted_path.split("."))

    return reduce(_getattr, attrs, module)


def require(*args: str):
    for arg in args:
        _ = import_string(arg)
