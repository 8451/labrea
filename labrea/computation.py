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
    """Abstract base class for effects.

    Effects are transformations that are applied to values, but do not return a new value.
    They are intended to encapsulate side effects, such as logging, data validation, or
    other operations that do not affect the value being returned by an Evaluatable.
    """

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
    """An effect that chains multiple effects together.

    This effect applies a sequence of effects to a value in order.

    Arguments
    ---------
    *effects : Effect
        The effects to chain together.
    """

    effects: List[Effect[A]]

    def __init__(self, *effects: Effect[A]):
        self.effects = list(effects)

    def transform(self, value: A, options: Optional[Options] = None) -> None:
        """Perform each effect in sequence."""
        for effect in self.effects:
            effect.transform(value, options)

    def validate(self, options: Options) -> None:
        """Validate each effect."""
        for effect in self.effects:
            effect.validate(options)

    def explain(self, options: Optional[Options] = None) -> Set[str]:
        """Return the option keys required to perform each effect."""
        return set().union(*(effect.explain(options) for effect in self.effects))

    def __repr__(self) -> str:
        return f"ChainedEffect({', '.join(map(repr, self.effects))})"


class CallbackEffect(Effect[A]):
    """An effect that applies a callback to a value.

    This allows any function of one value to be used as an effect. The
    callback can also be an Evaluatable that returns a function,
    which allows :code:`Pipeline` objects to be used as effects.

    Arguments
    ---------
    callback : MaybeEvaluatable[Callable[[A], None]]
        The callback to apply to the value. Either a function of one
        value that returns None, or an Evaluatable that returns such
        a function.
    """

    callback: Evaluatable[Callable[[A], None]]

    def __init__(self, callback: MaybeEvaluatable[Callable[[A], None]]):
        self.callback = Evaluatable.ensure(callback)

    def transform(self, value: A, options: Optional[Options] = None) -> None:
        """Apply the callback to the value."""
        self.callback(options)(value)

    def validate(self, options: Options) -> None:
        """Validate the callback."""
        self.callback.validate(options)

    def explain(self, options: Optional[Options] = None) -> Set[str]:
        """Return the option keys required to perform the callback."""
        return self.callback.explain(options)

    def __repr__(self) -> str:
        return f"CallbackEffect({self.callback!r})"


class Computation(Evaluatable[A]):
    """A computation that applies an effect to a value.

    This class combines an Evaluatable with an Effect to create a new
    Evaluatable that applies the effect to the value returned by the
    original Evaluatable. This allows side effects to be applied to
    values without modifying the original Evaluatable.

    If the :code:`LABREA.EFFECTS.DISABLED` option is set to True, the
    effect will not be applied to the value. This allows the effect to
    be disabled in certain contexts, such as testing or debugging.


    Arguments
    ---------
    evaluatable : Evaluatable[A]
        The Evaluatable to apply the effect to.
    effect : Effect[A]
        The Effect to apply to the value returned by the Evaluatable.
    """

    evaluatable: Evaluatable[A]
    effect: Effect[A]

    def __init__(self, evaluatable: Evaluatable[A], effect: Effect[A]):
        self.evaluatable = evaluatable
        self.effect = effect

    def evaluate(self, options: Options) -> A:
        """Evaluate the Evaluatable and apply the Effect to the result before returning."""
        value = self.evaluatable.evaluate(options)

        if not _EFFECTS_DISABLED(options):
            self.effect.transform(value, options)

        return value

    def validate(self, options: Options) -> None:
        """Validate the Evaluatable and the Effect."""
        self.evaluatable.validate(options)

        if not _EFFECTS_DISABLED(options):
            self.effect.validate(options)

    def keys(self, options: Options) -> Set[str]:
        """Return the option keys required to evaluate the Evaluatable."""
        return self.evaluatable.keys(options)

    def explain(self, options: Optional[Options] = None) -> Set[str]:
        """Return the option keys required to evaluate the Evaluatable and apply the Effect."""
        return (
            self.evaluatable.explain(options)
            if _EFFECTS_DISABLED(options)
            else self.evaluatable.explain(options) | self.effect.explain(options)
        )

    def __repr__(self) -> str:
        return f"Computation({self.evaluatable!r}, {self.effect!r})"
