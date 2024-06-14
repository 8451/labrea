from abc import ABC, abstractmethod
from copy import deepcopy
from typing import Callable, Generic, Optional, Set, TypeVar, Union

from .types import Cacheable, Explainable, Options, Validatable

A = TypeVar("A", covariant=True)
B = TypeVar("B", covariant=True)
T = TypeVar("T")


class EvaluationError(Exception):
    """Error raised when an object cannot be evaluated."""

    msg: str
    source: "Evaluatable"

    def __init__(self, msg: str, source: "Evaluatable") -> None:
        self.msg = msg
        self.source = source

        super().__init__(msg, source)

    def __str__(self):
        return f"Originating in {self.source} | {self.msg}"


class KeyNotFoundError(EvaluationError):
    """Error raised when a key is not found in the options dictionary."""

    key: str
    source: "Evaluatable"

    def __init__(self, key: str, source: "Evaluatable") -> None:
        self.key = key

        super().__init__(f"Key '{self.key}' not found", source)


class InsufficientInformationError(EvaluationError):
    """Error raised when not enough information is provided to explain an object."""

    def __init__(self, reason: str, source: "Evaluatable") -> None:
        super().__init__(
            f"Insufficient information to evaluate {source}: {reason}", source
        )


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
            The evaluated value.

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
        """Wrap a value in a Value object.

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
        return Apply(self, self.ensure(func))

    def bind(self, func: Callable[[A], "Evaluatable[B]"]) -> "Evaluatable[B]":
        return Bind(self, func)


MaybeEvaluatable = Union[Evaluatable[A], A]


class Value(Evaluatable[A]):
    """Simple wrapper for a plain value.

    This class is used to wrap a value that is not an Evaluatable and make it
    an Evaluatable.

    Arguments
    ----------
    value : A
        The value to wrap.
    """

    value: A

    def __init__(self, value: A) -> None:
        self.value = value

    def evaluate(self, options: Options) -> A:
        """Evaluate the object.

        Returns the value that was wrapped. If possible, the value is deep
        copied.
        """
        try:
            return deepcopy(self.value)
        except Exception:  # noqa: E722
            return self.value

    def validate(self, options: Options) -> None:
        """Validate the object.

        This method does nothing, as the value can always be evaluated.
        """
        pass

    def keys(self, options: Options) -> Set[str]:
        """Return the keys that this object depends on.

        This method returns an empty set, as the value does not depend on any
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
