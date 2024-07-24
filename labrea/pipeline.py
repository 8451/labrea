import sys

if sys.version_info < (3, 10):
    from typing_extensions import Concatenate, ParamSpec
else:
    from typing import Concatenate, ParamSpec

from typing import (
    Any,
    Callable,
    Generic,
    Iterable,
    Iterator,
    Optional,
    Set,
    TypeVar,
    cast,
    overload,
)

from .application import PartialApplication
from .types import Evaluatable, MaybeEvaluatable, Options, Transformation, Value

A = TypeVar("A")
B = TypeVar("B", covariant=True)
C = TypeVar("C")
P = ParamSpec("P")


class PipelineStep(Evaluatable[Callable[[A], B]], Transformation[A, B]):
    """A class representing a single step in a pipeline.

    A pipeline step is a single transformation that can be applied to a value.
    Steps can be composed into pipelines using the :code:`+` operator.

    This class should probably not be used directly. Instead, use the :code:`pipeline_step`
    """

    step: Evaluatable[Callable[[A], B]]
    _name: Optional[str]

    def __init__(
        self, step: Evaluatable[Callable[[A], B]], _name: Optional[str] = None
    ) -> None:
        self.step = step
        self._name = _name

    def evaluate(self, options: Options) -> Callable[[A], B]:
        """Evaluate the pipeline step, returning a function that applies the transformation."""
        return self.step.evaluate(options)

    def validate(self, options: Options) -> None:
        """Validate the pipeline step."""
        self.step.validate(options)

    def keys(self, options: Options) -> Set[str]:
        """Return the option keys required by the pipeline step."""
        return self.step.keys(options)

    def explain(self, options: Optional[Options] = None) -> Set[str]:
        """Return the option keys required by the pipeline step."""
        return self.step.explain(options)

    def transform(self, value: A, options: Optional[Options] = None) -> B:
        """Transform a value using the pipeline step.

        Arguments
        ---------
        value : A
            The value to transform.
        options : Optional[Options]
            The options to use when transforming the value.

        Returns
        -------
        B
            The transformed value.
        """
        return self(options)(value)

    def __repr__(self) -> str:
        return f"<PipelineStep {self._name or repr(self.step)}>"

    def __add__(self, other: MaybeEvaluatable[Callable[[B], C]]) -> "Pipeline[A, C]":
        base: Pipeline[A, B] = Pipeline(self)
        return base + other

    def __eq__(self, other: Any) -> bool:
        return isinstance(other, PipelineStep) and self.step == other.step


class _Identity(Generic[A], PipelineStep[A, A]):
    def __new__(cls) -> "_Identity[A]":
        return super().__new__(cls)

    def __init__(self) -> None:
        super().__init__(Value(lambda x: x), "Identity")


Identity: _Identity = _Identity()


class Pipeline(
    Evaluatable[Callable[[A], B]],
    Iterable[Evaluatable[Callable[[Any], Any]]],
    Transformation[A, B],
):
    """A class representing a pipeline of transformations.

    A pipeline is a sequence of transformations that can be applied to a value.
    Pipelines are implemented as a linked list of PipelineSteps, where each step
    is a single transformation that can be applied to a value. Pipelines, like
    PipelineSteps, can be composed using the :code:`+` operator.

    This class should probably not be used directly. Instead, use the :code:`pipeline_step`
    and compose pipelines using the :code:`+` operator.
    """

    tail: PipelineStep[Any, B]
    rest: Optional["Pipeline[A, Any]"]

    @overload
    def __new__(cls) -> "Pipeline[A, A]":
        ...  # pragma: nocover

    @overload
    def __new__(cls, tail: PipelineStep[B, C]) -> "Pipeline[B, C]":
        ...  # pragma: nocover

    @overload
    def __new__(
        cls, tail: PipelineStep[B, C], rest: "Pipeline[A, B]"
    ) -> "Pipeline[A, C]":
        ...  # pragma: nocover

    def __new__(
        cls,
        tail: PipelineStep[B, C] = Identity,
        rest: Optional["Pipeline[A, B]"] = None,
    ):
        return super().__new__(cls)

    def __init__(
        self,
        tail: PipelineStep[Any, B] = Identity,
        rest: Optional["Pipeline[A, Any]"] = None,
    ) -> None:
        if rest is not None and rest.empty:
            rest = None

        self.tail = tail
        self.rest = rest

    def evaluate(self, options: Options) -> Callable[[A], B]:
        """Evaluate the pipeline, returning a function that applies all transformations."""
        tail = self.tail.evaluate(options)
        rest = self.rest.evaluate(options) if self.rest else lambda x: x
        return lambda x: tail(rest(x))

    def validate(self, options: Options) -> None:
        """Validate the pipeline."""
        self.tail.validate(options)
        if self.rest:
            self.rest.validate(options)

    def keys(self, options: Options) -> Set[str]:
        """Return the option keys required by the pipeline."""
        return self.tail.keys(options) | (
            self.rest.keys(options) if self.rest else set()
        )

    def explain(self, options: Optional[Options] = None) -> Set[str]:
        """Return the option keys required by the pipeline."""
        return self.tail.explain(options) | (
            self.rest.explain(options) if self.rest else set()
        )

    def transform(self, value: A, options: Optional[Options] = None) -> B:
        """Transform a value using the pipeline."""
        return self(options)(value)

    def __repr__(self) -> str:
        if self.empty:
            return "<Pipeline Identity>"
        return f'<Pipeline {" + ".join(map(repr, self))}>'

    def __add__(self, other: MaybeEvaluatable[Callable[[B], C]]) -> "Pipeline[A, C]":
        if isinstance(other, PipelineStep):
            return Pipeline(other, self)
        elif isinstance(other, Pipeline):
            if other.empty:
                return cast(Pipeline[A, C], self)
            elif other.rest is None:
                return Pipeline(other.tail, self)
            return (self + other.rest) + other.tail
        else:
            return Pipeline(PipelineStep(Evaluatable.ensure(other)), self)

    def __iter__(self) -> Iterator[Evaluatable[Callable[[Any], Any]]]:
        if self.rest is not None:
            yield from self.rest
        yield self.tail

    @property
    def empty(self) -> bool:
        return self.tail == Identity and self.rest is None


def pipeline_step(func: Callable[Concatenate[A, P], B]) -> "PipelineStep[A, B]":
    """Create a pipeline step from a function.

    This is the primary way to create a pipeline step. The function should be used
    as a decorator on the function that will be used as the transformation. The
    function should take at least one argument. The first argument will be the value
    to transform; the remaining arguments will be the parameters for the transformation,
    and should have default values similar to a dataset definition.


    Example Usage
    -------------
    >>> @pipeline_step
    ... def add(x: int, y: int = Option('AMOUNT', 1)) -> int:
    ...     return x + y
    >>>
    >>> @pipeline_step
    ... def multiply(x: int, y: int = Option('FACTOR', 2)) -> int:
    ...     return x * y
    >>>
    >>> pipeline = add + multiply
    >>> pipeline.transform(1)
    4
    >>> pipeline.transform(1, {'AMOUNT': 2, 'FACTOR': 3})
    9
    """
    return PipelineStep(PartialApplication.lift(func), getattr(func, "__name__", None))
