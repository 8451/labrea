from typing import Dict, List, Set, TypeVar

from .types import Evaluatable, JSONDict

A = TypeVar("A")
K = TypeVar("K")


class DatasetList(Evaluatable[List[A]]):
    """A list of Evaluatables that can be evaluated as a list of values

    Turns a list of Evaluatables into a single Evaluatable that evaluates to a
    list of values.
    """

    contents: List[Evaluatable[A]]

    def __init__(self, *contents: Evaluatable[A]):
        """Create a new DatasetList Evaluatable

        Parameters
        ----------
        *contents : Evaluatable[A]
            The Evaluatables to include in the list.
        """
        self.contents = list(contents)

    def evaluate(self, options: JSONDict) -> List[A]:
        """Evaluate the Evaluatables in the list

        Return a list containing the results of evaluating each Evaluatable in
        the list.

        See Also
        --------
        labrea.types.Evaluatable.evaluate
        """
        return [dep.evaluate(options) for dep in self.contents]

    def validate(self, options: JSONDict):
        """Validate each Evaluatable in the list.

        See Also
        --------
        labrea.types.Validatable.validate
        """
        for val in self.contents:
            val.validate(options)

    def keys(self, options: JSONDict) -> Set[str]:
        """Return the keys that each Evaluatable in the list depends on.

        See Also
        --------
        labrea.types.Validatable.keys
        """
        return {key for val in self.contents for key in val.keys(options)}

    def __repr__(self):
        return f'DatasetList({", ".join(map(repr, self.contents))})'


class DatasetDict(Evaluatable[Dict[K, A]]):
    """A dict of Evaluatables that can be evaluated as a dict of values

    Turns a dict of Evaluatables into a single Evaluatable that evaluates to a
    dict of values.
    """

    contents: Dict[K, Evaluatable[A]]

    def __init__(self, contents: Dict[K, Evaluatable[A]]):
        """Create a new DatasetDict Evaluatable

        Parameters
        ----------
        contents : Dict[K, Evaluatable[A]]
            The Evaluatables to include in the dict.
        """
        self.contents = contents.copy()

    def evaluate(self, options: JSONDict) -> Dict[K, A]:
        """Evaluate the Evaluatables in the dict

        Return a dict containing the results of evaluating each Evaluatable in
        the dict.

        See Also
        --------
        labrea.types.Evaluatable.evaluate
        """
        return {key: val.evaluate(options) for key, val in self.contents.items()}

    def validate(self, options: JSONDict):
        """Validate each Evaluatable in the dict values.

        See Also
        --------
        labrea.types.Validatable.validate
        """
        for val in self.contents.values():
            val.validate(options)

    def keys(self, options: JSONDict) -> Set[str]:
        """Return the keys that each Evaluatable in the dict values depends on.

        See Also
        --------
        labrea.types.Validatable.keys
        """
        return {key for val in self.contents.values() for key in val.keys(options)}

    def __repr__(self):
        return f"DatasetDict({repr(self.contents)})"
