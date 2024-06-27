from . import _version
from .application import FunctionApplication
from .arguments import (
    Arguments,
    EvaluatableArgs,
    EvaluatableArguments,
    EvaluatableKwargs,
)
from .cache import cached
from .coalesce import Coalesce
from .collections import (
    DatasetDict,
    DatasetList,
    DatasetSet,
    DatasetTuple,
    evaluatable_dict,
    evaluatable_list,
    evaluatable_set,
    evaluatable_tuple,
)
from .computation import Computation
from .conditional import Switch, case, switch
from .dataset import Dataset, abstractdataset, dataset
from .datasetclass import datasetclass
from .evaluatable import (
    Evaluatable,
    EvaluationError,
    InsufficientInformationError,
    KeyNotFoundError,
    MaybeEvaluatable,
    Options,
    Value,
)
from .interface import implements, interface
from .iterable import Iter
from .option import Option, WithOptions
from .overload import Overloaded, overloaded
from .template import Template

__version__ = _version.__version__


__all__ = [
    "FunctionApplication",
    "Arguments",
    "EvaluatableArgs",
    "EvaluatableArguments",
    "EvaluatableKwargs",
    "cached",
    "Coalesce",
    "evaluatable_dict",
    "evaluatable_list",
    "evaluatable_set",
    "evaluatable_tuple",
    "DatasetDict",
    "DatasetList",
    "DatasetSet",
    "DatasetTuple",
    "Computation",
    "case",
    "Switch",
    "switch",
    "Dataset",
    "abstractdataset",
    "dataset",
    "datasetclass",
    "Evaluatable",
    "EvaluationError",
    "InsufficientInformationError",
    "KeyNotFoundError",
    "MaybeEvaluatable",
    "Options",
    "Value",
    "interface",
    "implements",
    "Iter",
    "Overloaded",
    "overloaded",
    "Option",
    "WithOptions",
    "Template",
]
