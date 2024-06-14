import hashlib
import json
from abc import ABC, abstractmethod
from typing import List, Mapping, Optional, Protocol, Set, TypeVar, Union

from confectioner.templating import get_dotted_key

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
        Return the keys from the Options that this object depends on.

        This should only return the keys that are present in the options dictionary.
        If a key is not present but is required, a KeyNotFoundError should be raised.

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

    def fingerprint(self, options: Options) -> bytes:
        """Return a fingerprint, which is a unique identifier for a given evaluation."""
        fingerprint = hashlib.blake2b(repr(self).encode(), digest_size=64)

        for key in sorted(self.keys(options)):
            fingerprint.update(key.encode())
            fingerprint.update(
                json.dumps(get_dotted_key(key, options), sort_keys=True).encode()
            )

        return fingerprint.digest()


class Explainable(ABC):
    @abstractmethod
    def explain(self, options: Optional[Options] = None) -> Set[str]:
        """Return all keys that this object depends on.

        This should return all keys that this object depends on, including those that are not
        present in the options dictionary. If the keys required cannot be determined, an
        InsufficientInformationError should be raised.

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
        InsufficientInformationError
            If the keys required cannot be determined.

        Notes
        -----
        This method should be called recursively on all child objects where
        applicable.
        """
