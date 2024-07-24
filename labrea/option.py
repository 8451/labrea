from typing import Callable, Optional, Set, TypeVar

from confectioner import mix
from confectioner.templating import dotted_key_exists, get_dotted_key, resolve

from ._missing import MISSING, MaybeMissing
from .application import FunctionApplication
from .exceptions import KeyNotFoundError
from .template import Template
from .types import JSON, Evaluatable, MaybeEvaluatable, Options

A = TypeVar("A", covariant=True, bound=JSON)
B = TypeVar("B", covariant=True)


class Option(Evaluatable[A]):
    """A class representing a single user-provided option.

    Options are the singular way to provide user-input to an Evaluatable
    object. They take a key, which is used to retrieve the value from the
    options dictionary. If the key does not exist, a default value can be
    provided.

    Arguments
    ----------
    key : str
        The key to retrieve from the options dictionary. This key can be
        nested using the standard :code:`{NESTED.KEY}` syntax from
        confectioner.
    default : MaybeEvaluatable[A]
        The default value to use if the key does not exist in the options
        dictionary. If the default value is an Evaluatable, it is evaluated
        using the options dictionary. If the default value is not an
        Evaluatable, it is returned as-is. If the default value is a string,
        it is treated as a :code:`Template` and evaluated using the options
        dictionary.
    default_factory : Callable[[], A]
        A factory function that returns the default value to use if the key
        does not exist in the options dictionary. This is an alternative to
        providing a default value directly.
    doc : str
        The docstring for the option.


    Example Usage
    -------------
    >>> from labrea import Option
    >>> o = Option('A.X', default='foo')
    >>> o()
    'foo'
    >>> o({'A': {'X': 'bar'}})
    'bar'
    """

    key: str
    default: MaybeMissing[Evaluatable[A]]

    def __init__(
        self,
        key: str,
        default: MaybeMissing[MaybeEvaluatable[A]] = MISSING,
        default_factory: MaybeMissing[Callable[[], A]] = MISSING,
        doc: str = "",
    ) -> None:
        self.key = key
        if isinstance(default, str):
            self.default = Template(default)  # type: ignore [assignment]
        elif default is not MISSING:
            self.default = Evaluatable.ensure(default)
        elif default_factory is not MISSING:
            self.default = FunctionApplication(default_factory)
        else:
            self.default = MISSING

        self.__doc__ = doc

    def evaluate(self, options: Options) -> A:
        """Retrieves the key from the options dictionary.

        If the key does not exist, the default key is returned. If no default
        key is provided, an error is raised. If the default key is an
        Evaluatable, it is evaluated using the options dictionary. If the
        default key is not an Evaluatable, it is returned as-is.
        """
        try:
            value = get_dotted_key(self.key, options)
            return resolve(value, options)
        except KeyError:
            if self.default is MISSING:
                raise KeyNotFoundError(self.key, self)
            return self.default.evaluate(options)

    def validate(self, options: Options) -> None:
        """Validates that the key exists in the options dictionary.

        If the key does not exist, the default key is validated. If the
        default key is an Evaluatable, it is validated using the options
        dictionary. If the default key is not an Evaluatable, it is ignored.
        """
        if dotted_key_exists(self.key, options):
            _ = self.keys(options)
        elif self.default is not MISSING:
            self.default.validate(options)
        else:
            raise KeyNotFoundError(self.key, self)

    def keys(self, options: Options) -> Set[str]:
        """Returns the keys required by the option.

        Usually this is just the provided key, but if the default value is a
        string, the keys required by the template are also returned. Similarly,
        if the default value is an Evaluatable, the keys required by the
        Evaluatable are also returned.
        """
        if dotted_key_exists(self.key, options):
            value = get_dotted_key(self.key, options)
            if isinstance(value, str):
                return {self.key} | Template(value).keys(options)
            else:
                return {self.key}
        elif self.default is not MISSING:
            return self.default.keys(options)
        else:
            raise KeyNotFoundError(self.key, self)

    def explain(self, options: Optional[Options] = None) -> Set[str]:
        """Returns the keys required by the option."""
        options = options or {}
        if dotted_key_exists(self.key, options):
            value = get_dotted_key(self.key, options)
            if isinstance(value, str):
                return {self.key} | Template(value).explain(options)
            else:
                return {self.key}
        elif self.default is not MISSING:
            return self.default.explain(options)
        else:
            return {self.key}

    def __repr__(self) -> str:
        return (
            f"Option({self.key!r}, default={self.default!r})"
            if self.default is not MISSING
            else f"Option({self.key!r})"
        )


class WithOptions(Evaluatable[B]):
    """A class that wraps an Evaluatable object and provides default options.

    This class is used to provide default options to an Evaluatable object. The
    default options are mixed with the provided options. The default options
    can be forced to take precedence over the provided options (default) or
    the provided options can take precedence over the default options.

    Arguments
    ----------
    evaluatable : Evaluatable[B]
        The evaluatable object to wrap.
    options : Options
        The default options to provide to the evaluatable object.
    force : bool, optional
        If True, the default options take precedence over the provided options.
        If False, the provided options take precedence over the default options.
        Default is True.
    """

    evaluatable: Evaluatable[B]
    options: Options
    force: bool

    def __init__(
        self, evaluatable: Evaluatable[B], options: Options, force: bool = True
    ) -> None:
        self.evaluatable = evaluatable
        self.options = options
        self.force = force

    def _options(self, options: Options) -> Options:
        return (
            mix(options, self.options)  # type: ignore
            if self.force
            else mix(self.options, options)  # type: ignore
        )

    def evaluate(self, options: Options) -> B:
        """Evaluate the wrapped Evaluatable object with the provided options."""
        return self.evaluatable.evaluate(self._options(options))

    def validate(self, options: Options) -> None:
        """Validate the wrapped Evaluatable object with the provided options."""
        self.evaluatable.validate(self._options(options))

    def keys(self, options: Options) -> Set[str]:
        """Return the keys required by the wrapped Evaluatable object."""
        return {
            key
            for key in self.evaluatable.keys(self._options(options))
            if not (
                dotted_key_exists(key, self.options)
                and (self.force or not dotted_key_exists(key, options))
            )
        }

    def explain(self, options: Optional[Options] = None) -> Set[str]:
        """Return the explanation for the wrapped Evaluatable object."""
        options = options or {}
        return {
            key
            for key in self.evaluatable.explain(self._options(options))
            if not (
                dotted_key_exists(key, self.options)
                and (self.force or not dotted_key_exists(key, options))
            )
        }

    def __repr__(self) -> str:
        return (
            f"WithOptions({self.evaluatable!r}, {self.options!r})"
            if self.force
            else f"WithDefaultOptions({self.evaluatable!r}, {self.options!r})"
        )


def WithDefaultOptions(evaluatable: Evaluatable[B], options: Options) -> WithOptions[B]:
    """Wrap an Evaluatable object with default options.

    This is a convenience function for creating a WithOptions object
    with :code:`force=False`.

    Arguments
    ----------
    evaluatable : Evaluatable[B]
        The evaluatable object to wrap.
    options : Options
        The default options to provide to the evaluatable object.

    Returns
    -------
    WithOptions[B]
        The wrapped evaluatable object with default options.
    """
    return WithOptions(evaluatable, options, force=False)
