import itertools
from typing import Dict, Iterable, Optional, Set, Tuple, TypeVar

from confectioner.templating import set_dotted_key

from .exceptions import EvaluationError
from .option import WithOptions
from .types import JSON, Evaluatable, MaybeEvaluatable, Options

A = TypeVar("A", covariant=True)


class Iter(Evaluatable[Iterable[A]]):
    """A class representing multiple evaluatables as an iterable.

    This is used to lazily evaluate multiple evaluatables in a single
    operation. The result is an iterable of the evaluated values.

    Arguments
    ----------
    *evaluatables : MaybeEvaluatable[A]
        The evaluatables to evaluate.


    Example Usage
    -------------
    >>> from labrea import Iter, Option
    >>> i = Iter(Option('A.X'), Option('B.Y'))
    >>> for value in i({'A': {'X': 1}, 'B': {'Y': 2}}):
    ...     print(value)
    1
    2
    """

    evaluatables: Iterable[Evaluatable[A]]

    def __init__(self, *evaluatables: Evaluatable[A]):
        self.evaluatables = tuple(Evaluatable.ensure(e) for e in evaluatables)

    def evaluate(self, options: Options) -> Iterable[A]:
        """Evaluate the evaluatables and return an iterable of the results."""
        return (evaluatable.evaluate(options) for evaluatable in self.evaluatables)

    def validate(self, options: Options) -> None:
        """Validate that all evaluatables can be evaluated."""
        for evaluatable in self.evaluatables:
            evaluatable.validate(options)

    def keys(self, options: Options) -> Set[str]:
        """Return the option keys required by the evaluatables."""
        return {
            key
            for evaluatable in self.evaluatables
            for key in evaluatable.keys(options)
        }

    def explain(self, options: Optional[Options] = None) -> Set[str]:
        """Return the option keys required by the evaluatables."""
        return {
            explanation
            for evaluatable in self.evaluatables
            for explanation in evaluatable.explain(options)
        }

    def __repr__(self) -> str:
        return f"Iter({', '.join(map(repr, self.evaluatables))})"


class Map(Evaluatable[Iterable[Tuple[Dict[str, JSON], A]]]):
    """A class that represents the same evaluatable repeated over multiple options.

    This is used to evaluate a single evaluatable multiple times with different
    options. The result is an iterable of tuples, where the first element is the
    options used to evaluate the evaluatable, and the second element is the
    evaluated value. This is the Labrea equivalent of a for loop.

    Arguments
    ---------
    evaluatable : Evaluatable[A]
        The evaluatable to evaluate.
    iterables : Dict[str, MaybeEvaluatable[Iterable[JSON]]]
        A dictionary mapping option keys to iterables of options. The keys
        can be dotted to represent nested options.


    Example Usage
    -------------
    >>> from labrea import Map, Option, dataset
    >>> @dataset
    ... def hypotenuse(a: int = Option('A'), b: int = Option('B')) -> float:
    ...     return (a ** 2 + b ** 2) ** 0.5
    >>>
    >>> hypotenuses = Map(hypotenuse, {'A': Option('X'), 'B': Option('Y')})
    >>> for options, value in hypotenuses({'X': [3, 4], 'Y': [4, 5]}):
    ...     print(options, value)
    {'A': 3, 'B': 4} 5.0
    {'A': 3, 'B': 5} 5.830951894845301
    {'A': 4, 'B': 4} 5.656854249492381
    {'A': 4, 'B': 5} 6.403124237432848
    """

    evaluatable: Evaluatable[A]
    iterables: Dict[str, Evaluatable[Iterable[JSON]]]

    def __init__(
        self,
        evaluatable: Evaluatable[A],
        iterables: Dict[str, MaybeEvaluatable[Iterable[JSON]]],
    ) -> None:
        self.evaluatable = evaluatable
        self.iterables = {
            key: Evaluatable.ensure(value) for key, value in iterables.items()
        }

    def evaluate(self, options: Options) -> Iterable[Tuple[Dict[str, JSON], A]]:
        """Evaluate the evaluatable with each set of options."""
        return self._iter(options).evaluate(options)

    def validate(self, options: Options) -> None:
        """Validate that both the option iterables and the evaluatable can be evaluated."""
        self._iter(options).validate(options)

    def keys(self, options: Options) -> Set[str]:
        """Return the option keys required by the evaluatable and the option iterables"""
        return set().union(
            self._iter(options).keys(options),
            *(iterable.keys(options) for iterable in self.iterables.values()),
        )

    def explain(self, options: Optional[Options] = None) -> Set[str]:
        """Return the option keys required by the evaluatable and the option iterables"""
        try:
            return set().union(
                self._iter(options or {}).explain(options),
                *(iterable.explain(options) for iterable in self.iterables.values()),
            )
        except EvaluationError:
            return (
                self.evaluatable.explain(options) - self.iterables.keys()
            ) | set().union(
                *(iterable.explain(options) for iterable in self.iterables.values())
            )

    def _iter(
        self, options: Options
    ) -> Evaluatable[Iterable[Tuple[Dict[str, JSON], A]]]:
        return Iter(
            *(
                Iter(
                    Iter(*option_tuples).apply(dict),  # type: ignore
                    WithOptions(  # type: ignore
                        self.evaluatable, self._create_option_set(*option_tuples)
                    ),
                ).apply(lambda x: tuple(x))
                for option_tuples in self._iterate_over_options(options)
            )
        )

    @staticmethod
    def _create_option_set(*args: Tuple[str, JSON]) -> Options:
        options: Dict[str, JSON] = {}
        for key, value in args:
            set_dotted_key(key, value, options)

        return options

    def _iterate_over_options(
        self, options: Options
    ) -> Tuple[Tuple[Tuple[str, JSON], ...], ...]:
        return tuple(
            tuple(zip(self.iterables.keys(), values))
            for values in itertools.product(
                *(iterable.evaluate(options) for iterable in self.iterables.values())
            )
        )

    def __repr__(self) -> str:
        return f"Iterate({self.evaluatable!r}, {self.iterables!r})"

    @property
    def values(self) -> Evaluatable[Iterable[A]]:
        """Strip the options from the results.

        This is a convenience method that returns an evaluatable that
        returns the second element of the tuples returned by the Map
        evaluatable.
        """
        return self.apply(lambda items: (item[1] for item in items))
