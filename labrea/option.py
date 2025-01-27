from typing import Callable, Dict, Generic, List, Mapping, Optional, Set, Type, TypeVar

from confectioner import mix
from confectioner.templating import dotted_key_exists, get_dotted_key, resolve

from ._missing import MISSING, MaybeMissing
from .application import FunctionApplication
from .exceptions import KeyNotFoundError
from .template import Template
from .types import JSON, Apply, Evaluatable, MaybeEvaluatable, Options

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

    @staticmethod
    def namespace(__namespace: Type) -> "Namespace":
        """Create an option namespace from a class definition"""
        return Namespace.from_type(__namespace)

    @staticmethod
    def auto(
        default: MaybeMissing[MaybeEvaluatable[A]] = MISSING,
        doc: str = "",
    ) -> "Option[A]":
        """Create an option in a namespace with an inferred key"""
        return _Auto(default, doc)  # type: ignore


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


class _AllOptions(Evaluatable[Options]):
    def evaluate(self, options: Options) -> Options:
        return resolve(options)

    def validate(self, options: Options) -> None:
        pass

    def keys(self, options: Options) -> Set[str]:
        return set(options.keys())

    def explain(self, options: Optional[Options] = None) -> Set[str]:
        return set() if options is None else set(options.keys())

    def __repr__(self) -> str:
        return "AllOptions"


AllOptions = _AllOptions()
AllOptions.__doc__ = """An object that evaluates to the entire options dictionary."""


class Namespace(Evaluatable[Options]):
    """Namespace for options that allows for better documentation and organization."""

    _key: str
    _full: Option
    _members: Mapping[str, Evaluatable]
    __doc__: str

    def __init__(self, key: str, members: Mapping[str, Evaluatable]) -> None:
        self._key = key
        self._full = Option(key, default={})
        self._members = members
        self.__doc__ = self._build_doc()

    def evaluate(self, options: Options) -> Options:
        return self._full.evaluate(options)

    def validate(self, options: Options) -> None:
        self._full.validate(options)

    def keys(self, options: Options) -> Set[str]:
        return self._full.keys(options)

    def explain(self, options: Optional[Options] = None) -> Set[str]:
        return self._full.explain(options)

    def __getitem__(self, key: str) -> Evaluatable:
        return self._members[key]

    def __getattr__(self, key: str) -> Evaluatable:
        try:
            return self._members[key]
        except KeyError:
            raise AttributeError(f"Namespace {self._key} has no attribute {key!r}")

    def __repr__(self) -> str:
        return f"Namespace({self._key!r})"

    @staticmethod
    def _build_doc_option(option: Option) -> str:
        doc = f"Option {option.key}"
        if option.default is not MISSING:
            doc += f" (default {option.default})"
        if option.__doc__:
            doc += ": " + "\n  ".join(option.__doc__.strip().splitlines())
        return doc

    def _build_doc(self) -> str:
        members = sorted(self._members.items(), key=lambda x: x[0])
        options: List[Option] = []
        namespaces: List[Namespace] = []

        for key, value in members:
            if isinstance(value, Namespace):
                namespaces.append(value)
            elif isinstance(value, Option):
                options.append(value)
            elif isinstance(value, Apply):
                while isinstance(value, Apply):
                    value = value.evaluatable
                if isinstance(value, Option):
                    options.append(value)
                else:
                    raise TypeError(
                        f"Namespace {self._key} has invalid member {key}: {value!r}"
                    )

        header = f"Namespace {self._key}:\n\n  "
        option_docs = (
            "\n  ".join(self._build_doc_option(opt).splitlines()) for opt in options
        )
        namespace_docs = (
            "\n  ".join((ns.__doc__ or "").splitlines()) + "\n" for ns in namespaces
        )

        return header + "\n  ".join((*option_docs, *namespace_docs)).rstrip()

    @classmethod
    def from_type(cls, __namespace: Type, parent: Optional[str] = None) -> "Namespace":
        key = f"{parent}.{__namespace.__name__}" if parent else __namespace.__name__

        members: Dict[str, Evaluatable] = {}
        for name in getattr(__namespace, "__annotations__", {}):
            members[name] = Option(f"{key}.{name}")
        for name, value in __namespace.__dict__.items():
            if name.startswith("_"):
                continue
            elif isinstance(value, Evaluatable):
                members[name] = value
            elif isinstance(value, type):
                members[name] = cls.from_type(value, parent=key)
            elif isinstance(value, _Auto):
                members[name] = value.build(f"{key}.{name}")
            else:
                members[name] = Option(f"{key}.{name}", default=value)

        return cls(key, members)


class _Auto(Generic[A]):
    default: MaybeMissing[MaybeEvaluatable[A]]
    doc: str
    transformations: List[Callable]

    def __init__(
        self,
        default: MaybeMissing[MaybeEvaluatable[A]] = MISSING,
        doc: str = "",
        *transformations: Callable,
    ) -> None:
        self.default = default
        self.doc = doc
        self.transformations = list(transformations)

    def build(self, key: str) -> Evaluatable[A]:
        option: Evaluatable = Option(key, self.default, doc=self.doc)
        for tform in self.transformations:
            option = option >> tform

        return option

    def __rshift__(self, func: MaybeEvaluatable[Callable[[A], B]]) -> Evaluatable[B]:
        return _Auto(self.default, self.doc, *self.transformations, func)  # type: ignore
