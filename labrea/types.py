from abc import ABC, abstractmethod
from typing import List, Mapping, Optional, Protocol, Set, TypeVar, Union

JSONScalar = Union[str, int, float, bool, None]
JSON = Union[JSONScalar, Mapping[str, "JSON"], List["JSON"]]
Options = Mapping[str, JSON]


A = TypeVar("A", contravariant=True)
B = TypeVar("B", covariant=True)


class Transformation(Protocol[A, B]):
    def __call__(self, value: A, options: Optional[Options] = None) -> B:
        ...  # pragma: nocover


class Validatable(ABC):
    @abstractmethod
    def validate(self, options: Options) -> None:
        """Validate the object.

        Arguments
        ----------
        options : Options
            The options dictionary to validate against.

        Raises
        ------
        KeyNotFoundError
            If a required key is not found in the options dictionary.

        Notes
        -----
        This method should be called recursively on all child objects where
        applicable.
        """
        raise NotImplementedError  # pragma: nocover


class Cacheable(ABC):
    @abstractmethod
    def keys(self, options: Options) -> Set[str]:
        """
        Return the keys that this object depends on.

        Arguments
        ----------
        options : Options
            The options dictionary to validate against.

        Returns
        -------
        Set[str]
            The keys that this object depends on.

        Raises
        ------
        KeyNotFoundError
            If a required key is not found in the options dictionary.

        Notes
        -----
        This method should be called recursively on all child objects where
        applicable.
        """
        raise NotImplementedError  # pragma: nocover
