import functools
import inspect
import sys
import warnings
from typing import Callable, Generic, Optional, TypeVar

from functional_pypelines.core import Pipeline
from functional_pypelines.validator import (
    FAILURE,
    SUCCESS,
    ValidationResult,
    ValidatorPipeline,
)

from .collections import DatasetDict
from .types import Evaluatable, JSONDict, ValidationError, Value

if sys.version_info < (3, 10):
    from typing_extensions import Concatenate, ParamSpec
else:
    from typing import Concatenate, ParamSpec


A = TypeVar("A")
B = TypeVar("B")
P = ParamSpec("P")


# -----------------------------------------------------------------------------
# Core of Labrea Pypeline
# -----------------------------------------------------------------------------
class LabreaPipelineData(Generic[A]):
    value: A
    options: JSONDict

    def __init__(self, value: A, options: Optional[JSONDict] = None):
        self.value = value
        self.options = options or {}

    def __eq__(self, other):
        if not isinstance(other, LabreaPipelineData):
            return False

        return (self.value, self.options) == (other.value, other.options)

    def __repr__(self):
        return (
            f"{self.__class__.__name__}("
            f"{repr(self.value)}, "
            f"options={repr(self.options)})"
        )


@Pipeline.step
def _unwrap_pipeline_data(data: LabreaPipelineData):
    return data.value


class LabreaPipeline(Pipeline[LabreaPipelineData[A], LabreaPipelineData[B]]):
    """Subclass of functional_pypelines.core.Pipeline for use with Labrea"""

    @staticmethod
    def default_data() -> LabreaPipelineData[None]:
        return LabreaPipelineData(None)

    @classmethod
    def step(cls, f: Callable[Concatenate[A, P], B]) -> "LabreaPipeline[A, B]":
        """Decorator to create a new LabreaPipeline step from a function

        LabreaPipeline steps are created similarly to Datasets, but with
        a single first argument with no default value. The first argument
        is the value of the previous step in the pipeline. All other arguments
        must have default values, which will be evaluated using the options
        dictionary passed to the pipeline.

        Example Usage
        -------------
        >>> from labrea import LabreaPipeline, Option
        >>> @LabreaPipeline.step
        ... def add_n(x: int, n: int = Option('N')) -> int:
        ...    return x + n
        >>>
        >>> @LabreaPipeline
        ... def multiply_by_m(x: int, m: int = Option('M')) -> int:
        ...    return x * m
        >>>
        >>> pipeline = add_n >> multiply_by_m
        >>> print(pipeline(1, options={'N': 2, 'M': 3})) # 9
        """
        signature = inspect.signature(f)
        for i, (key, val) in enumerate(signature.parameters.items()):
            if i == 0 and val.default is not signature.empty:
                warnings.warn(
                    f"Argument {key} has default value {val.default} that "
                    f"that will be ignored",
                    stacklevel=2,
                )
            elif i > 0 and val.default is signature.empty:
                raise TypeError(f"Argument {key} must have a default value")
        kwargs = DatasetDict(
            {
                key: (
                    val.default
                    if isinstance(val.default, Evaluatable)
                    else Value(val.default)
                )
                for key, val in list(signature.parameters.items())[1:]
            }
        )

        @functools.wraps(f)
        def _step(data: LabreaPipelineData[A]) -> LabreaPipelineData[B]:
            return LabreaPipelineData(
                f(
                    data.value,  # type: ignore [arg-type]
                    **kwargs.evaluate(data.options),
                ),
                data.options,
            )

        setattr(_step, "_labrea_kwargs", kwargs)

        return cls(_step)

    @classmethod
    def wrap(cls, *args, **kwargs) -> "LabreaPipelineData":
        if len(args) and isinstance(args[0], LabreaPipelineData):
            return args[0]
        elif len(args) == 0 and "value" not in kwargs:
            return LabreaPipelineData(None, **kwargs)

        return LabreaPipelineData(*args, **kwargs)

    @property
    def base_validator(self) -> ValidatorPipeline:
        return validator

    unwrap = _unwrap_pipeline_data


# -----------------------------------------------------------------------------
# Validator Steps
# -----------------------------------------------------------------------------
@ValidatorPipeline.step
def validator(pipeline: LabreaPipeline, data: LabreaPipelineData) -> ValidationResult:
    for step in pipeline:
        try:
            step_kwargs: DatasetDict = getattr(
                step, "_labrea_kwargs", DatasetDict({})  # type: ignore [arg-type]
            )
            step_kwargs.validate(data.options)
        except ValidationError as e:
            return FAILURE(e.args[0])

    return SUCCESS
