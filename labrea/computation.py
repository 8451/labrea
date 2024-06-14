from abc import ABC, abstractmethod
from typing import Callable, Generic, Optional, Set, TypeVar

from .evaluatable import Evaluatable
from .types import Explainable, Options, Transformation, Validatable

A = TypeVar("A", contravariant=True)
B = TypeVar("B", covariant=True)


class Effect(Transformation[A, B], Validatable, Explainable, ABC):
    @abstractmethod
    def __call__(self, value: A, options: Optional[Options] = None) -> B:
        """Apply the effect to a value.

        Arguments
        ----------
        value : A
            The value to apply the effect to.
        options : Options
            The options dictionary to evaluate against.

        Returns
        -------
        A
            The value after the effect has been applied.

        Raises
        ------
        EvaluationError
            If the effect cannot be applied to the value.
        """
        raise NotImplementedError  # pragma: nocover


class UnvalidatedEffect(Effect[A, B]):
    func: Callable[[A], B]

    def __init__(self, func: Callable[[A], B]):
        self.func = func

    def __call__(self, value: A, options: Optional[Options] = None) -> B:
        return self.func(value)

    def validate(self, options: Options) -> None:
        pass

    def explain(self, options: Optional[Options] = None) -> Set[str]:
        return set()


class Computation(Generic[A, B], Evaluatable[B]):
    evaluatable: Evaluatable[A]
    effect: Effect[A, B]

    def __init__(self, evaluatable: Evaluatable[A], effect: Effect[A, B]):
        self.evaluatable = evaluatable
        self.effect = effect

    def evaluate(self, options: Options) -> B:
        value = self.evaluatable.evaluate(options)
        return self.effect(value, options)

    def validate(self, options: Options) -> None:
        self.evaluatable.validate(options)
        self.effect.validate(options)

    def keys(self, options: Options) -> Set[str]:
        return self.evaluatable.keys(options)

    def explain(self, options: Optional[Options] = None) -> Set[str]:
        return self.evaluatable.explain(options) | self.effect.explain(options)

    def __repr__(self) -> str:
        return f"Computation({self.evaluatable!r}, {self.effect!r})"
