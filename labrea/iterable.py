from typing import Iterable, Optional, Set, TypeVar

from .evaluatable import Evaluatable, MaybeEvaluatable
from .types import Options

A = TypeVar("A", covariant=True)


class Iter(Evaluatable[Iterable[A]]):
    """A class representing multiple evaluatables as an iterable."""

    evaluatables: Iterable[Evaluatable[A]]

    def __init__(self, *evaluatables: MaybeEvaluatable[A]):
        self.evaluatables = tuple(Evaluatable.ensure(e) for e in evaluatables)

    def evaluate(self, options: Options) -> Iterable[A]:
        return (evaluatable.evaluate(options) for evaluatable in self.evaluatables)

    def validate(self, options: Options) -> None:
        for evaluatable in self.evaluatables:
            evaluatable.validate(options)

    def keys(self, options: Options) -> Set[str]:
        return {
            key
            for evaluatable in self.evaluatables
            for key in evaluatable.keys(options)
        }

    def explain(self, options: Optional[Options] = None) -> Set[str]:
        return {
            explanation
            for evaluatable in self.evaluatables
            for explanation in evaluatable.explain(options)
        }

    def __repr__(self) -> str:
        return f"Iter({', '.join(map(repr, self.evaluatables))})"
