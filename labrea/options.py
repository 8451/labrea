from typing import Callable, Set, TypeVar, Union

from confectioner.templating import dotted_key_exists, get_dotted_key, resolve

from .template import Template
from .types import Evaluatable, EvaluationError, JSONDict, ValidationError, Value

A = TypeVar("A")


MaybeEvaluatableA = Union[A, Evaluatable[A]]


class Unreachable(Evaluatable[A]):
    def evaluate(self, options: JSONDict) -> A:
        raise EvaluationError("UNREACHABLE")  # pragma: nocover

    def validate(self, options: JSONDict) -> None:
        raise ValidationError("UNREACHABLE")  # pragma: nocover

    def keys(self, options: JSONDict) -> Set[str]:
        return set()  # pragma: nocover


_UNREACHABLE: Evaluatable = Unreachable()


class Option(Evaluatable[A]):
    """Retrieves a single entry from the options dictionary.

    If the key does not exist, the default value is returned. If no default
    value is provided, an error is raised. If the default value is an
    Evaluatable, it is evaluated using the options dictionary. If the
    default value is not an Evaluatable, it is returned as-is. A
    default_factory can be provided instead of a default value.

    Parameters
    ----------
    key : str
        The key to retrieve from the options dictionary.
    default : Evaluatable[A] | A, optional
        The default value to return if the key does not exist
        in the options dictionary
    default_factory : Callable[[], Evaluatable[A] | A], optional
        A function that returns the default value to return if the key
        does not exist in the options dictionary.
    doc : str, optional
        The docstring for the Option object
    """

    key: str
    default: Evaluatable[A]
    default_factory: Callable[[], MaybeEvaluatableA] = lambda: _UNREACHABLE

    def __init__(
        self,
        key: str,
        default: MaybeEvaluatableA = _UNREACHABLE,
        default_factory: Callable[[], MaybeEvaluatableA] = lambda: _UNREACHABLE,
        doc: str = "",
    ):
        if default is _UNREACHABLE:
            default = default_factory()

        if isinstance(default, str):
            default = Template(default)
        elif not isinstance(default, Evaluatable):
            default = Value(default)

        self.key = key
        self.default = default  # type: ignore [assignment]
        self.default_factory = default_factory
        self.__doc__ = doc

    def evaluate(self, options: JSONDict) -> A:
        """Retrieves the value from the options dictionary.

        If the key does not exist, the default value is returned. If no default
        value is provided, an error is raised. If the default value is an
        Evaluatable, it is evaluated using the options dictionary. If the
        default value is not an Evaluatable, it is returned as-is.
        """
        try:
            value = get_dotted_key(self.key, options)
            if self.resolving(options):
                return resolve(value, options)
            else:
                return value
        except KeyError:
            if not self.has_default:
                raise EvaluationError(self.key)
            return self.default.evaluate(options)

    def validate(self, options: JSONDict) -> None:
        """
        Validates that the key exists in the options dictionary, or that
        a default value is provided and can be validated against the options
        dictionary.
        """
        if not self.has_default and not dotted_key_exists(self.key, dict(options)):
            raise ValidationError(self.key)

        if self.resolving(options):
            try:
                resolve(get_dotted_key(self.key, options), options)
            except KeyError as e:
                if self.has_default:
                    self.default.validate(options)
                else:
                    raise ValidationError(self.key) from e

    def keys(self, options: JSONDict) -> Set[str]:
        """Returns the keys that this object depends on.

        This method returns the key that this object depends on, if it exists
        in the options dictionary. If the key does not exist, the default keys
        are returned.
        """
        return (
            {self.key}
            if dotted_key_exists(self.key, dict(options))
            else self.default.keys(options)
        )

    @property
    def has_default(self):
        return self.default is not _UNREACHABLE

    @staticmethod
    def resolving(options: JSONDict) -> bool:
        return (
            options.get("LABREA", {})  # type: ignore
            .get("OPTIONS", {})
            .get("RESOLVE", True)
        )
