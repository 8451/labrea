import sys
from copy import deepcopy
from dataclasses import dataclass
from typing import Callable, List, Mapping, Optional, Set, TypeVar, Union

# Support Python < 3.8
if sys.version_info >= (3, 8):  # pragma: nocover
    from typing import Protocol, runtime_checkable
else:  # pragma: nocover
    from typing_extensions import Protocol, runtime_checkable


JSONScalar = Union[int, float, bool, str, None]
JSONType = Union[JSONScalar, "JSONDict", List["JSONType"]]  # type: ignore
JSONDict = Mapping[str, JSONType]  # type: ignore


Alias = JSONScalar
MultiAlias = List[Alias]


A = TypeVar("A", covariant=True)
B = TypeVar("B", covariant=True)


@runtime_checkable
class Validatable(Protocol):
    """A protocol for objects that can be validated.

    This protocol is used to validate objects that are not yet evaluated.
    """

    def validate(self, options: JSONDict) -> None:
        """Validate the object.

        Parameters
        ----------
        options : JSONDict
            The options dictionary to validate against.

        Raises
        ------
        ValidationError
            If the object is invalid.

        Notes
        -----
        This method should be called recursively on all child objects where
        applicable.
        """
        raise NotImplementedError  # pragma: nocover

    def keys(self, options: JSONDict) -> Set[str]:
        """
        Return the keys that this object depends on.

        Parameters
        ----------
        options : JSONDict
            The options dictionary to validate against.

        Returns
        -------
        Set[str]
            The keys that this object depends on.

        Notes
        -----
        This method should be called recursively on all child objects where
        applicable.
        """
        raise NotImplementedError  # pragma: nocover


@runtime_checkable
class Evaluatable(Validatable, Protocol[A]):
    """A protocol for objects that can be evaluated.

    This protocol is used to define a common interface for objects that can be
    evaluated using an options dictionary. Datasets, Options, and other types
    defined in this library implement this protocol.
    """

    def __call__(self, options: JSONDict) -> A:
        """Evaluate the object.

        Any object that explicitly inherits from Evaluatble can be called as a
        function

        Parameters
        ----------
        options : JSONDict
            The options dictionary to evaluate against.

        Returns
        -------
        A
            The evaluated value.

        Raises
        ------
        EvaluationError
            If the object cannot be evaluated.
        """
        return self.evaluate(options)

    def evaluate(self, options: JSONDict) -> A:
        """Evaluate the object.

        Parameters
        ----------
        options : JSONDict
            The options dictionary to evaluate against.

        Returns
        -------
        A
            The evaluated value.

        Raises
        ------
        EvaluationError
            If the object cannot be evaluated.

        Notes
        -----
        This method should be called recursively on all child objects where
        applicable.
        """
        raise NotImplementedError  # pragma: nocover

    @property
    def result(self) -> A:
        """Dummy property to allow for type checking.

        This property is used to allow for type checking of the return value of
        an Evaluatable. At runtime, it simply returns the Evaluatable itself.
        """
        return self  # type: ignore


Callback = Callable[[A, JSONDict], Optional[B]]
Callback.__doc__ = """A callback function

Callbacks will be used to extend the behavior of an Evaluatable, either by
running a computation before or after the .evaluate() method is called.
"""


@dataclass
class Value(Evaluatable[A]):
    """Simple wrapper for a plain value.

    This class is used to wrap a value that is not an Evaluatable and make it
    an Evaluatable.

    Parameters
    ----------
    value : A
        The value to wrap.
    """

    value: A

    def evaluate(self, options: JSONDict) -> A:
        """Evaluate the object.

        Returns the value that was wrapped. If possible, the value is deep
        copied.
        """
        try:
            return deepcopy(self.value)
        except Exception:  # noqa: E722
            return self.value

    def validate(self, options: JSONDict) -> None:
        """Validate the object.

        This method does nothing, as the value can always be evaluated.
        """
        pass

    def keys(self, options: JSONDict) -> Set[str]:
        """Return the keys that this object depends on.

        This method returns an empty set, as the value does not depend on any
        keys.
        """
        return set()


class EvaluationError(ValueError):
    """Error raised when an object cannot be evaluated."""

    pass  # pragma: nocover


class ValidationError(KeyError):
    """Error raised when an object cannot be validated.

    This error is raised when an object cannot be validated against an options
    dictionary. This means that we can statically determine that the object
    cannot be evaluated, usually due to a missing key in the options
    dictionary.
    """

    pass  # pragma: nocover
