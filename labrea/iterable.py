import itertools
from typing import Dict, Iterable, Optional, Set, Tuple, TypeVar

from confectioner.templating import set_dotted_key

from .exceptions import EvaluationError
from .option import WithOptions
from .types import JSON, Evaluatable, MaybeEvaluatable, Options

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


class Map(Evaluatable[Iterable[Tuple[Dict[str, JSON], A]]]):
    """A class that represents the same evaluatable repeated over multiple options."""

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
        return self._iter(options).evaluate(options)

    def validate(self, options: Options) -> None:
        self._iter(options).validate(options)

    def keys(self, options: Options) -> Set[str]:
        return set().union(
            self._iter(options).keys(options),
            *(iterable.keys(options) for iterable in self.iterables.values()),
        )

    def explain(self, options: Optional[Options] = None) -> Set[str]:
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
        return self.apply(lambda items: (item[1] for item in items))
