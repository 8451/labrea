import hashlib
import json
from abc import ABC, abstractmethod
from copy import deepcopy
from typing import (
    Callable,
    Generic,
    List,
    Mapping,
    Optional,
    Protocol,
    Set,
    TypeVar,
    Union,
)

from confectioner.templating import get_dotted_key

from .exceptions import EvaluationError, InsufficientInformationError

JSONScalar = Union[str, int, float, bool, None]
JSON = Union[JSONScalar, Mapping[str, "JSON"], List["JSON"]]
Options = Mapping[str, JSON]


A = TypeVar("A", covariant=True)
B = TypeVar("B", covariant=True)
R = TypeVar("R", covariant=True)
T = TypeVar("T", contravariant=True)


class Transformation(Protocol[T, R]):
    def transform(self, value: T, options: Optional[Options] = None) -> R:
        raise NotImplementedError  # pragma: nocover


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
        fingerprint = hashlib.blake2b(digest_size=64)

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


class Evaluatable(Generic[A], Cacheable, Explainable, Validatable, ABC):
    """A protocol for objects that can be evaluated.

    This protocol is used to define a common interface for objects that can be
    evaluated using an options dictionary. Datasets, Options, and other types
    defined in this library implement this protocol.
    """

    def __call__(self, options: Optional[Options] = None) -> A:
        """Evaluate the object.

        Any object that explicitly inherits from Evaluatable can be called as a
        function

        Arguments
        ----------
        options : Options
            The options dictionary to evaluate against.

        Returns
        -------
        A
            The evaluated key.

        Raises
        ------
        KeyNotFoundError
            If a required key is not found in the options dictionary.
        """
        return self.evaluate(options or {})

    @abstractmethod
    def evaluate(self, options: Options) -> A:
        """Evaluate the object.

        Arguments
        ----------
        options : Options
            The options dictionary to evaluate against.

        Returns
        -------
        A
            The evaluated key.

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

    @abstractmethod
    def __repr__(self) -> str:
        """Return a string representation of the object.

        Returns
        -------
        str
            A string representation of the object.
        """
        raise NotImplementedError  # pragma: nocover

    @staticmethod
    def unit(value: T) -> "Value[T]":
        """Wrap a key in a Value object.

        This method is used to wrap a value in a Value object. This is useful
        when you want to treat a value as an Evaluatable.

        Arguments
        ----------
        value : A
            The value to wrap.

        Returns
        -------
        Value[A]
            The wrapped value.
        """
        return Value(value)

    @staticmethod
    def ensure(value: "MaybeEvaluatable[T]") -> "Evaluatable[T]":
        """Ensure that a value is an Evaluatable.

        This method is used to ensure that a value is an Evaluatable. If the
        value is already an Evaluatable, it is returned as is. If the value is
        not an Evaluatable, it is wrapped in a Value object.

        Arguments
        ----------
        value : MaybeEvaluatable[A]
            The value to ensure is an Evaluatable.

        Returns
        -------
        Evaluatable[A]
            The value as an Evaluatable.
        """
        if isinstance(value, Evaluatable):
            return value
        return Value(value)

    def apply(self, func: "MaybeEvaluatable[Callable[[A], B]]") -> "Evaluatable[B]":
        if not isinstance(func, Evaluatable) and not callable(func):
            raise TypeError(f"Cannot apply object of type ({type(func)})")

        return Apply(self, self.ensure(func))

    def bind(self, func: Callable[[A], "Evaluatable[B]"]) -> "Evaluatable[B]":
        if not callable(func):
            raise TypeError(f"Cannot bind object of type ({type(func)})")
        return Bind(self, func)

    @property
    def result(self) -> A:
        return self  # type: ignore

    def __rshift__(
        self, other: "MaybeEvaluatable[Callable[[A], B]]"
    ) -> "Evaluatable[B]":
        return self.apply(other)


class Value(Evaluatable[A]):
    """Simple wrapper for a plain key.

    This class is used to wrap a key that is not an Evaluatable and make it
    an Evaluatable.

    Arguments
    ----------
    value : A
        The key to wrap.
    """

    value: A

    def __init__(self, value: A) -> None:
        self.value = value

    def evaluate(self, options: Options) -> A:
        """Evaluate the object.

        Returns the key that was wrapped. If possible, the key is deep
        copied.
        """
        try:
            return deepcopy(self.value)
        except Exception:  # noqa: E722
            return self.value

    def validate(self, options: Options) -> None:
        """Validate the object.

        This method does nothing, as the key can always be evaluated.
        """
        pass

    def keys(self, options: Options) -> Set[str]:
        """Return the keys that this object depends on.

        This method returns an empty set, as the key does not depend on any
        keys.
        """
        return set()

    def explain(self, options: Optional[Options] = None) -> Set[str]:
        return set()

    def __repr__(self) -> str:
        return f"Value({self.value!r})"

    def __eq__(self, other):
        return isinstance(other, Value) and self.value == other.value


class Apply(Generic[A, B], Evaluatable[B]):
    evaluatable: Evaluatable[A]
    func: Evaluatable[Callable[[A], B]]

    def __init__(
        self, evaluatable: Evaluatable[A], func: Evaluatable[Callable[[A], B]]
    ) -> None:
        self.evaluatable = evaluatable
        self.func = func

    def evaluate(self, options: Options) -> B:
        return self.func(options)(self.evaluatable(options))

    def validate(self, options: Options) -> None:
        self.evaluatable.validate(options)
        self.func.validate(options)

    def keys(self, options: Options) -> Set[str]:
        return self.evaluatable.keys(options) | self.func.keys(options)

    def explain(self, options: Optional[Options] = None) -> Set[str]:
        return self.evaluatable.explain(options) | self.func.explain(options)

    def __repr__(self) -> str:
        return f"{self.evaluatable!r}.apply({self.func!r})"


class Bind(Generic[A, B], Evaluatable[B]):
    evaluatable: Evaluatable[A]
    func: Callable[[A], Evaluatable[B]]

    def __init__(
        self, evaluatable: Evaluatable[A], func: Callable[[A], Evaluatable[B]]
    ) -> None:
        self.evaluatable = evaluatable
        self.func = func

    def evaluate(self, options: Options) -> B:
        return self.func(self.evaluatable(options)).evaluate(options)

    def validate(self, options: Options) -> None:
        self.evaluatable.validate(options)
        self.func(self.evaluatable(options)).validate(options)

    def keys(self, options: Options) -> Set[str]:
        return self.evaluatable.keys(options) | self.func(
            self.evaluatable(options)
        ).keys(options)

    def explain(self, options: Optional[Options] = None) -> Set[str]:
        try:
            return self.evaluatable.explain(options) | self.func(
                self.evaluatable(options)
            ).explain(options)
        except EvaluationError as e:
            raise InsufficientInformationError(f"Cannot explain {self}", self) from e

    def __repr__(self) -> str:
        return f"{self.evaluatable!r}.bind({self.func!r})"


MaybeEvaluatable = Union[Evaluatable[A], A]
