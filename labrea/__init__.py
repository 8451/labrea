from . import _version
from .application import FunctionApplication
from .arguments import (
    Arguments,
    EvaluatableArgs,
    EvaluatableArguments,
    EvaluatableKwargs,
)
from .coalesce import Coalesce
from .computation import Computation
from .conditional import Switch, switch
from .option import Option
from .template import Template

__version__ = _version.__version__


__all__ = [
    "FunctionApplication",
    "Arguments",
    "EvaluatableArgs",
    "EvaluatableArguments",
    "EvaluatableKwargs",
    "Coalesce",
    "Computation",
    "Switch",
    "switch",
    "Option",
    "Template",
]
