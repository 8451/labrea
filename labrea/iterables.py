import itertools
from typing import Dict, Iterable, List, Optional, Set, Tuple, TypeVar

from confectioner import mix
from confectioner.templating import set_dotted_key

from .types import Evaluatable, EvaluationError, JSONDict, JSONType, ValidationError

A = TypeVar("A")


class Map(Evaluatable[Iterable[A]]):
    """A map over a dataset

    A map is a dataset that is evaluated multiple times with different options. The options are
    updated with the values of iterables, which are iterated over. The map will evaluate the dataset
    for each combination of the iterables, and return a list of the results.
    """

    dataset: Evaluatable[A]
    iterables: Dict[str, Evaluatable[Iterable[JSONType]]]

    def __init__(
        self,
        dataset: Evaluatable[A],
        iterables: Optional[Dict[str, Evaluatable[Iterable]]] = None,
    ):
        self.dataset = dataset
        self.iterables = iterables or {}

    def evaluate(self, options: JSONDict) -> List[A]:
        return [
            self.dataset.evaluate(updated_options)
            for updated_options in self._iterate_over_options(options)
        ]

    def validate(self, options: JSONDict) -> None:
        for iterable in self.iterables.values():
            iterable.validate(options)

        for updated_options in self._iterate_over_options(options):
            try:
                self.dataset.validate(updated_options)
            except EvaluationError as e:
                raise ValidationError from e

    def keys(self, options: JSONDict) -> Set[str]:
        iterable_keys = set.union(
            *(iterable.keys(options) for iterable in self.iterables.values())
        )

        dataset_keys = set.union(
            *(
                self.dataset.keys(updated_options) - set(self.iterables.keys())
                for updated_options in self._iterate_over_options(options)
            )
        )

        return iterable_keys | dataset_keys

    @staticmethod
    def _update_options(options: JSONDict, *args: Tuple[str, JSONType]) -> JSONDict:
        new_options: JSONDict = {}
        for key, value in args:
            set_dotted_key(key, value, new_options)  # type: ignore

        return mix(options, new_options)  # type: ignore

    @staticmethod
    def _iterate_over_option(
        key: str, iterable: Evaluatable[Iterable[JSONType]], options: JSONDict
    ) -> Iterable[Tuple[str, JSONType]]:
        return ((key, value) for value in iterable.evaluate(options))

    def _iterate_over_options(self, options) -> Iterable[JSONDict]:
        return (
            self._update_options(options, *args)
            for args in itertools.product(
                *(
                    self._iterate_over_option(key, iterable, options)
                    for key, iterable in self.iterables.items()
                )
            )
        )

    def over(self, iterables: Dict[str, Evaluatable[Iterable[JSONType]]]) -> "Map":
        """Create a new map over the supplied iterables

        If the map does not yet have any iterables, the new map will be created with the supplied
        iterables. If the map already has iterables, the new map will map the existing map over
        the supplied iterables, in effect creating a nested map.

        Parameters
        ----------
            iterables : Dict[str, Evaluatable[Iterable[JSONType]]]
                A dictionary of iterables to map over. Keys are the which entries in the options
                dictionary to update, and values are the iterables to iterate over. If the key is
                dotted, the value will be nested in the options dictionary.

        Returns
        -------
            Map[A]
        """
        if not self.iterables:
            return Map(self.dataset, iterables)
        else:
            return Map(self, iterables)
