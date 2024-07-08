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
    Union,
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
    step: Evaluatable[Callable[[A], B]]
    _name: Optional[str]

    def __init__(
        self, step: Evaluatable[Callable[[A], B]], _name: Optional[str] = None
    ) -> None:
        self.step = step
        self._name = _name

    def evaluate(self, options: Options) -> Callable[[A], B]:
        return self.step.evaluate(options)

    def validate(self, options: Options) -> None:
        self.step.validate(options)

    def keys(self, options: Options) -> Set[str]:
        return self.step.keys(options)

    def explain(self, options: Optional[Options] = None) -> Set[str]:
        return self.step.explain(options)

    def transform(self, value: A, options: Optional[Options] = None) -> B:
        return self(options)(value)

    def __repr__(self) -> str:
        return f"<PipelineStep {self._name or repr(self.step)}>"

    def __add__(
        self, other: Union["Pipeline[B, C]", "PipelineStep[B, C]"]
    ) -> "Pipeline[A, C]":
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
        tail = self.tail.evaluate(options)
        rest = self.rest.evaluate(options) if self.rest else lambda x: x
        return lambda x: tail(rest(x))

    def validate(self, options: Options) -> None:
        self.tail.validate(options)
        if self.rest:
            self.rest.validate(options)

    def keys(self, options: Options) -> Set[str]:
        return self.tail.keys(options) | (
            self.rest.keys(options) if self.rest else set()
        )

    def explain(self, options: Optional[Options] = None) -> Set[str]:
        return self.tail.explain(options) | (
            self.rest.explain(options) if self.rest else set()
        )

    def transform(self, value: A, options: Optional[Options] = None) -> B:
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
    return PipelineStep(PartialApplication.lift(func), getattr(func, "__name__", None))
