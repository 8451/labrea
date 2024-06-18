from abc import ABC, abstractmethod
from typing import Callable, Generic, List, Optional, Set, TypeVar

from .evaluatable import Evaluatable
from .types import Explainable, Options, Transformation, Validatable

A = TypeVar("A")
B = TypeVar("B")


class Effect(Transformation[A, B], Validatable, Explainable, ABC):
    @abstractmethod
    def __call__(self, value: A, options: Optional[Options] = None) -> B:
        """Apply the effect to a key.

        Arguments
        ----------
        value : A
            The key to apply the effect to.
        options : Options
            The options dictionary to evaluate against.

        Returns
        -------
        A
            The key after the effect has been applied.

        Raises
        ------
        EvaluationError
            If the effect cannot be applied to the key.
        """
        raise NotImplementedError  # pragma: nocover


class ChainedEffect(Effect[A, A]):
    effects: List[Effect[A, A]]

    def __init__(self, *effects: Effect[A, A]):
        self.effects = list(effects)

    def __call__(self, value: A, options: Optional[Options] = None) -> A:
        for effect in self.effects:
            value = effect(value, options)
        return value

    def validate(self, options: Options) -> None:
        for effect in self.effects:
            effect.validate(options)

    def explain(self, options: Optional[Options] = None) -> Set[str]:
        return set().union(*(effect.explain(options) for effect in self.effects))

    def __repr__(self) -> str:
        return f"ChainedEffect({', '.join(map(repr, self.effects))})"


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

    def __repr__(self) -> str:
        return f"UnvalidatedEffect({self.func!r})"


class CallbackEffect(Effect[A, B]):
    callback: Callable[[A, Options], B]

    def __init__(self, callback: Callable[[A, Options], B]):
        self.callback = callback

    def __call__(self, value: A, options: Optional[Options] = None) -> B:
        return self.callback(value, options or {})

    def validate(self, options: Options) -> None:
        pass

    def explain(self, options: Optional[Options] = None) -> Set[str]:
        return set()

    def __repr__(self) -> str:
        return f"Callback({self.callback!r})"


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
