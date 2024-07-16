from abc import ABC, abstractmethod
from typing import Callable, List, Optional, Set, TypeVar

from .option import Option
from .types import (
    Evaluatable,
    Explainable,
    MaybeEvaluatable,
    Options,
    Transformation,
    Validatable,
)

A = TypeVar("A")

_EFFECTS_DISABLED = Option("LABREA.EFFECTS.DISABLED", False)


class Effect(Transformation[A, None], Validatable, Explainable, ABC):
    @abstractmethod
    def transform(self, value: A, options: Optional[Options] = None) -> None:
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


class ChainedEffect(Effect[A]):
    effects: List[Effect[A]]

    def __init__(self, *effects: Effect[A]):
        self.effects = list(effects)

    def transform(self, value: A, options: Optional[Options] = None) -> None:
        for effect in self.effects:
            effect.transform(value, options)

    def validate(self, options: Options) -> None:
        for effect in self.effects:
            effect.validate(options)

    def explain(self, options: Optional[Options] = None) -> Set[str]:
        return set().union(*(effect.explain(options) for effect in self.effects))

    def __repr__(self) -> str:
        return f"ChainedEffect({', '.join(map(repr, self.effects))})"


class CallbackEffect(Effect[A]):
    callback: Evaluatable[Callable[[A], None]]

    def __init__(self, callback: MaybeEvaluatable[Callable[[A], None]]):
        self.callback = Evaluatable.ensure(callback)

    def transform(self, value: A, options: Optional[Options] = None) -> None:
        return self.callback(options)(value)

    def validate(self, options: Options) -> None:
        self.callback.validate(options)

    def explain(self, options: Optional[Options] = None) -> Set[str]:
        return self.callback.explain(options)

    def __repr__(self) -> str:
        return f"CallbackEffect({self.callback!r})"


class Computation(Evaluatable[A]):
    evaluatable: Evaluatable[A]
    effect: Effect[A]

    def __init__(self, evaluatable: Evaluatable[A], effect: Effect[A]):
        self.evaluatable = evaluatable
        self.effect = effect

    def evaluate(self, options: Options) -> A:
        value = self.evaluatable.evaluate(options)

        if not _EFFECTS_DISABLED(options):
            self.effect.transform(value, options)

        return value

    def validate(self, options: Options) -> None:
        self.evaluatable.validate(options)

        if not _EFFECTS_DISABLED(options):
            self.effect.validate(options)

    def keys(self, options: Options) -> Set[str]:
        return self.evaluatable.keys(options)

    def explain(self, options: Optional[Options] = None) -> Set[str]:
        return (
            self.evaluatable.explain(options)
            if _EFFECTS_DISABLED(options)
            else self.evaluatable.explain(options) | self.effect.explain(options)
        )

    def __repr__(self) -> str:
        return f"Computation({self.evaluatable!r}, {self.effect!r})"
