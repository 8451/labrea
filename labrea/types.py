import json
from abc import ABC, abstractmethod
from copy import deepcopy
from typing import (
    Callable,
    Generic,
    Mapping,
    Optional,
    Protocol,
    Sequence,
    Set,
    TypeVar,
    Union,
    overload,
)

from confectioner.templating import get_dotted_key

from .exceptions import EvaluationError, InsufficientInformationError
from .runtime import Request

JSONScalar = Union[str, int, float, bool, None]
JSON = Union[JSONScalar, Mapping[str, "JSON"], Sequence["JSON"]]
Options = Mapping[str, JSON]


A = TypeVar("A", covariant=True)
B = TypeVar("B", covariant=True)
R = TypeVar("R", covariant=True)
T = TypeVar("T", contravariant=True)
X = TypeVar("X")


class Transformation(Protocol[T, R]):
    """A protocol for objects that can transform values using an options dictionary."""

    def transform(self, value: T, options: Optional[Options] = None) -> R:
        raise NotImplementedError  # pragma: nocover


class Validatable(ABC):
    """Abstract base class for objects that can be validated against an options dictionary."""

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

    def __labrea_validate__(self, options: Options) -> None:
        raise NotImplementedError

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)

        if not hasattr(cls.validate, "__labrea_wrapper__"):

            def validate(self, options: Options) -> None:
                return ValidateRequest(self, options).run()

            setattr(validate, "__labrea_wrapper__", True)

            cls.__labrea_validate__ = cls.validate
            cls.validate = validate


class Cacheable(ABC):
    """Abstract base class for objects that can be cached."""

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
        return json.dumps(
            [{key: get_dotted_key(key, options)} for key in sorted(self.keys(options))]
        ).encode()

    def __labrea_keys__(self, options: Options) -> Set[str]:
        raise NotImplementedError

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)

        if not hasattr(cls.keys, "__labrea_wrapper__"):

            def keys(self, options: Options) -> Set[str]:
                return KeysRequest(self, options).run()

            setattr(keys, "__labrea_wrapper__", True)

            cls.__labrea_keys__ = cls.keys
            cls.keys = keys


class Explainable(ABC):
    """Abstract base class for objects that can explain themselves."""

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

    def __labrea_explain__(self, options: Optional[Options] = None) -> Set[str]:
        raise NotImplementedError

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)

        if not hasattr(cls.explain, "__labrea_wrapper__"):

            def explain(self, options: Optional[Options] = None) -> Set[str]:
                return ExplainRequest(self, options or {}).run()

            setattr(explain, "__labrea_wrapper__", True)

            cls.__labrea_explain__ = cls.explain
            cls.explain = explain


class Evaluatable(Generic[A], Cacheable, Explainable, Validatable, ABC):
    """Abstract base class for objects that can be evaluated with an Options dictionary.

    This ABC is used to define a common interface for objects that can be
    evaluated using an options dictionary. Datasets, Options, and other types
    defined in this library implement subclass this ABC. This allows for
    polymorphic behavior when evaluating objects, and allows for third-party
    extensions to be created that can be used within the labrea framework.
    """

    def __call__(self, options: Optional[Options] = None) -> A:
        """Evaluate the object.

        An alias for the evaluate method, but can be called with no arguments.

        Arguments
        ----------
        options : Optional[Options]
            The options dictionary to evaluate against. An empty dictionary is
            used if no options are provided

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

    @overload
    @staticmethod
    def ensure(value: "Evaluatable[T]") -> "Evaluatable[T]": ...

    @overload
    @staticmethod
    def ensure(value: T) -> "Evaluatable[T]": ...

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
        """Lazy application of a function to the result of evaluating the object.

        This method is used to apply a function to the result of evaluating the
        object. The function is not evaluated until the object is evaluated.
        Equivalently can use the :code:`>>` operator.

        Arguments
        ----------
        func : MaybeEvaluatable[Callable[[A], B]]
            The function to apply to the result of evaluating the object. Either a
            function of one argument, or an Evaluatable that evaluates to a function
            of one argument.

        Returns
        -------
        Evaluatable[B]
            A new evaluatable, that when evaluated, applies the function to the
            result of evaluating the source object.


        Example Usage
        -------------
        >>> from labrea import Option
        >>>
        >>> Option('A').apply(str.upper)({'A': 'foo'})
        'FOO'
        >>>
        >>> (Option('B') >> str.upper)({'B': 'bar'})
        'BAR'
        """
        if not isinstance(func, Evaluatable) and not callable(func):
            raise TypeError(f"Cannot apply object of type ({type(func)})")

        return Apply(self, self.ensure(func))

    def bind(self, func: Callable[[A], "Evaluatable[B]"]) -> "Evaluatable[B]":
        """Lazy bind a function to the result of evaluating the object.

        This method is used to bind a function to the result of evaluating the
        object. The function should take the result of evaluating the object,
        and return an Evaluatable. This is useful for when you want to use the
        result of evaluating the object to determine the next step in the
        evaluation process.

        Arguments
        ----------
        func : Callable[[A], Evaluatable[B]]
            The function to bind to the result of evaluating the object.

        Returns
        -------
        Evaluatable[B]
            A new evaluatable, that when evaluated, binds the function to the
            result of evaluating the source object.

        Example Usage
        -------------
        >>> from labrea import Option
        >>>
        >>> x_if_a_neg_else_y = Option('A').bind(lambda a: Option('X') if a < 0 else Option('Y'))
        >>> x_if_a_neg_else_y({'A': -1, 'X': 'foo', 'Y': 'bar'})
        'foo'
        >>> x_if_a_neg_else_y({'A': 1, 'X': 'foo', 'Y': 'bar'})
        'bar'
        """
        if not callable(func):
            raise TypeError(f"Cannot bind object of type ({type(func)})")
        return Bind(self, func)

    @property
    def result(self) -> A:
        """Dummy property used to appease type checkers.

        When creating a dataset, type checkers will complain that the default
        values are not of the correct type. This property is used to tell the
        type checker that the default value is of the correct type.
        """
        return self  # type: ignore

    def __rshift__(
        self, other: "MaybeEvaluatable[Callable[[A], B]]"
    ) -> "Evaluatable[B]":
        return self.apply(other)

    def __labrea_evaluate__(self, options: Options) -> A:
        raise NotImplementedError

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)

        if not hasattr(cls.evaluate, "__labrea_wrapper__"):

            def evaluate(self, options: Options) -> A:
                return EvaluateRequest(self, options).run()

            setattr(evaluate, "__labrea_wrapper__", True)

            cls.__labrea_evaluate__ = cls.evaluate
            cls.evaluate = evaluate


class Value(Evaluatable[A]):
    """Simple wrapper for a plain value.

    This class is used to wrap a value that is not an Evaluatable and make it
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
        """Return the wrapped value."""
        try:
            return deepcopy(self.value)
        except Exception:  # noqa: E722
            return self.value

    def validate(self, options: Options) -> None:
        """Always passes validation."""
        pass

    def keys(self, options: Options) -> Set[str]:
        """Return an empty set, as this object does not depend on any keys."""
        return set()

    def explain(self, options: Optional[Options] = None) -> Set[str]:
        """Return an empty set, as this object does not depend on any keys."""
        return set()

    def __repr__(self) -> str:
        return f"Value({self.value!r})"

    def __eq__(self, other):
        return isinstance(other, Value) and self.value == other.value


class Apply(Generic[A, B], Evaluatable[B]):
    """A class representing the application of a function to the result of evaluating an object.

    This class is used to apply a function to the result of evaluating an object.
    Apply objects are not usually created directly, instead the :code:`apply` method
    is used on an Evaluatable object.
    """

    evaluatable: Evaluatable[A]
    func: Evaluatable[Callable[[A], B]]

    def __init__(
        self, evaluatable: Evaluatable[A], func: Evaluatable[Callable[[A], B]]
    ) -> None:
        self.evaluatable = evaluatable
        self.func = func

    def evaluate(self, options: Options) -> B:
        """Apply the function to the result of evaluating the object."""
        value = self.evaluatable(options)
        return self.func(options)(value)

    def validate(self, options: Options) -> None:
        """Validate the source object and the function to apply to it."""
        self.evaluatable.validate(options)
        self.func.validate(options)

    def keys(self, options: Options) -> Set[str]:
        """Return the keys the source object and the function depend on."""
        return self.evaluatable.keys(options) | self.func.keys(options)

    def explain(self, options: Optional[Options] = None) -> Set[str]:
        """Return the keys the source object and the function depend on."""
        return self.evaluatable.explain(options) | self.func.explain(options)

    def __repr__(self) -> str:
        return f"{self.evaluatable!r}.apply({self.func!r})"


class Bind(Generic[A, B], Evaluatable[B]):
    """A class representing the binding of a function to the result of evaluating an object.

    This class is used to bind a function to the result of evaluating an object.
    Bind objects are not usually created directly, instead the :code:`bind` method
    is used on an Evaluatable object.
    """

    evaluatable: Evaluatable[A]
    func: Callable[[A], Evaluatable[B]]

    def __init__(
        self, evaluatable: Evaluatable[A], func: Callable[[A], Evaluatable[B]]
    ) -> None:
        self.evaluatable = evaluatable
        self.func = func

    def evaluate(self, options: Options) -> B:
        """Bind the function to the result of evaluating the object."""
        return self.func(self.evaluatable(options)).evaluate(options)

    def validate(self, options: Options) -> None:
        """Validate the source object and the function"""
        self.evaluatable.validate(options)
        self.func(self.evaluatable(options)).validate(options)

    def keys(self, options: Options) -> Set[str]:
        """Return the keys the source object, function, and result depend on.

        Because the function is bound to the result of evaluating the source object,
        the source object must be evaluated to determine the keys that the function's
        result depends on.
        """
        return self.evaluatable.keys(options) | self.func(
            self.evaluatable(options)
        ).keys(options)

    def explain(self, options: Optional[Options] = None) -> Set[str]:
        """Return the keys the source object, function, and result depend on.

        Because the function is bound to the result of evaluating the source object,
        the source object must be evaluated to determine the keys that the function's
        result depends on.
        """
        try:
            return self.evaluatable.explain(options) | self.func(
                self.evaluatable(options)
            ).explain(options)
        except EvaluationError as e:
            raise InsufficientInformationError(f"Cannot explain {self}", self) from e

    def __repr__(self) -> str:
        return f"{self.evaluatable!r}.bind({self.func!r})"


MaybeEvaluatable = Union[Evaluatable[X], X]


class EvaluateRequest(Request[A]):
    """Request to evaluate an Evaluatable object.

    This request is used to evaluate an Evaluatable object with a given options dictionary.
    By default, the Evaluatable object is evaluated using the :code:`evaluate` method.
    """

    evaluatable: Evaluatable[A]
    options: Options

    def __init__(self, evaluatable: Evaluatable, options: Options):
        self.evaluatable = evaluatable
        self.options = options


class ValidateRequest(Request[None]):
    """Request to validate a Validatable object.

    This request is used to validate a Validatable object with a given options dictionary.
    By default, the Validatable object is validated using the :code:`validate` method.
    """

    validatable: Validatable
    options: Options

    def __init__(self, validatable: Validatable, options: Options):
        self.validatable = validatable
        self.options = options


class KeysRequest(Request[Set[str]]):
    """Request to get the keys that a Cacheable object depends on.

    This request is used to get the keys that a Cacheable object depends on with a given options
    dictionary. By default, the Cacheable object is evaluated using the :code:`keys` method.
    """

    cacheable: Cacheable
    options: Options

    def __init__(self, cacheable: Cacheable, options: Options):
        self.cacheable = cacheable
        self.options = options


class ExplainRequest(Request[Set[str]]):
    """Request to get the keys that an Explainable object depends on.

    This request is used to get the keys that an Explainable object depends on with a given options
    dictionary. By default, the Explainable object is evaluated using the :code:`explain` method.
    """

    explainable: Explainable
    options: Options

    def __init__(self, explainable: Explainable, options: Options):
        self.explainable = explainable
        self.options = options


class CaughtEvaluationError(EvaluationError):
    """An evaluation error that has been caught and re-raised.

    This error is used to indicate that an evaluation error has been caught and re-raised.
    It is used to provide additional context about the error, such as the source of the error.
    """

    def __init__(
        self, msg: str, source: Evaluatable, cause: Optional[BaseException]
    ) -> None:
        super().__init__(msg, source)
        self.__cause__ = cause


@EvaluateRequest.handle
def _evaluate_request(request: EvaluateRequest[A]) -> A:
    try:
        return request.evaluatable.__labrea_evaluate__(request.options)
    except Exception as e:
        raise e from CaughtEvaluationError(
            "Error during evaluation", request.evaluatable, e.__cause__
        )


@ValidateRequest.handle
def _validate_request(request: ValidateRequest) -> None:
    return request.validatable.__labrea_validate__(request.options)


@KeysRequest.handle
def _keys_request(request: KeysRequest) -> Set[str]:
    return request.cacheable.__labrea_keys__(request.options)


@ExplainRequest.handle
def _explain_request(request: ExplainRequest) -> Set[str]:
    return request.explainable.__labrea_explain__(request.options)
