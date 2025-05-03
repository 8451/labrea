import functools
import warnings
from typing import (
    Any,
    Callable,
    Container,
    Dict,
    Generic,
    List,
    Mapping,
    Optional,
    Set,
    Type,
    TypeVar,
    Union,
    cast,
    overload,
)

from confectioner import mix
from confectioner.templating import (
    dotted_key_exists,
    get_dotted_key,
    resolve,
    set_dotted_key,
)

from ._missing import MISSING, MaybeMissing
from .application import FunctionApplication
from .exceptions import KeyNotFoundError
from .template import Template
from .type_validation import TypeValidationRequest
from .types import JSON, Evaluatable, MaybeEvaluatable, Options, Value

A = TypeVar("A", covariant=True, bound="JSON")
B = TypeVar("B", covariant=True)
T = TypeVar("T", bound=JSON)
T_type = TypeVar("T_type", bound=Type)
_Domain = Union[Container[A], Callable[[A], bool]]
Domain = Evaluatable[_Domain]


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
    type: Type[A]
        The expected type of the option. Third-party packages can handle the
        :class:`labrea.type_validation.TypeValidationRequest` to enforce
        types
    domain: MaybeMissing[MaybeEvaluatable[_Domain]]
        A domain representing valid values for the option. The domain can be
        a predicate function, a container of valid values, or an Evaluatable
        that returns a predicate function or container of valid values
        (e.g. a pipeline step).


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
    type: Type[A]
    domain: MaybeMissing[Domain]

    def __init__(
        self,
        key: str,
        default: MaybeMissing[MaybeEvaluatable[A]] = MISSING,
        default_factory: MaybeMissing[Callable[[], A]] = MISSING,
        type: Type[A] = cast(Type, Any),
        domain: MaybeMissing[MaybeEvaluatable[_Domain]] = MISSING,
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

        self.type = type

        if domain is not MISSING:
            if not callable(domain) and not isinstance(
                domain, (Container, Evaluatable)
            ):
                raise TypeError(
                    f"{domain!r} cannot be used as a domain. "
                    f"Domain must be a callable, Container, "
                    f"or aan Evaluatable returning a callable or Container."
                )
            self.domain = Evaluatable.ensure(domain)
        else:
            self.domain = MISSING

        self.__doc__ = doc

    def _enforce_domain(self, value: Any, options: Options) -> None:
        if self.domain is MISSING:
            return

        domain = self.domain.evaluate(options)
        if not callable(domain) and not isinstance(domain, Container):
            warnings.warn(
                f"Domain {domain!r} for option {self.key} is not valid",
                RuntimeWarning,
            )
            return
        if callable(domain) and not domain(value):
            raise ValueError(
                f"Value {value!r} for option {self.key} does not satisfy {self.domain!r}"
            )
        if isinstance(domain, Container) and value not in domain:
            raise ValueError(
                f"Value {value!r} for option {self.key} not in domain {domain!r}"
            )

    def evaluate(self, options: Options) -> A:
        """Retrieves the key from the options dictionary.

        If the key does not exist, the default key is returned. If no default
        key is provided, an error is raised. If the default key is an
        Evaluatable, it is evaluated using the options dictionary. If the
        default key is not an Evaluatable, it is returned as-is.
        """
        try:
            value = resolve(get_dotted_key(self.key, options), options)
        except KeyError:
            if self.default is MISSING:
                raise KeyNotFoundError(self.key, self)
            value = self.default.evaluate(options)

        TypeValidationRequest(value, self.type, options).run()
        self._enforce_domain(value, options)

        return value

    def validate(self, options: Options) -> None:
        """Validates that the key exists in the options dictionary.

        If the key does not exist, the default key is validated. If the
        default key is an Evaluatable, it is validated using the options
        dictionary. If the default key is not an Evaluatable, it is ignored.
        """
        if dotted_key_exists(self.key, options):
            _ = self.evaluate(options)
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

    def __class_getitem__(cls, type: Any):
        return functools.partial(cls, type=type)

    @overload
    @staticmethod
    def namespace(__namespace: T_type) -> T_type: ...  # pragma: no cover

    @overload
    @staticmethod
    def namespace(
        __namespace: str,
    ) -> Callable[[T_type], T_type]: ...  # pragma: no cover

    @staticmethod
    def namespace(
        __namespace: Union[T_type, str],
    ) -> Union["Namespace", Callable[[T_type], T_type]]:
        """Create an option namespace from a class definition

        This allows all of the options for a module to be grouped together. Namespaces can contain
        :class:`Option` objects or other namespaces.

        When developing a package with Labrea, it is recommended to create an option namespace for
        with the same name as the package to avoid conflicts with other packages.

        To create options with docstrings, see :meth:`Option.auto`.

        Example Usage
        -------------
        >>> from labrea import Option
        >>> @Option.namespace
        ... class MY_PACKAGE:
        ...     class MODULE_1:    # Implicit sub-namespace
        ...         A: str  # Equivalent to Option('MY_PACKAGE.MODULE_1.A')
        ...     @Option.namespace("MODULE-2")
        ...     class MODULE_2:    # Explicit sub-namespace with custom name
        ...         A = 10  # Equivalent to Option('MY_PACKAGE.MODULE_1.A', 10)
        ...
        >>> MY_PACKAGE.MODULE_2.A()
        10
        >>> MY_PACKAGE.MODULE_2.A({'MY_PACKAGE': {'MODULE-2': {'A': 20}}})
        20
        >>> print(MY_PACKAGE.__doc__)
        Namespace MY_PACKAGE:
            Namespace MY_PACKAGE.MODULE_1:
                Option MY_PACKAGE.MODULE_1.A
            Namespace MY_PACKAGE.MODULE-2:
                Option MY_PACKAGE.MODULE-2.A (default 10)
        """
        if isinstance(__namespace, str):
            return lambda cls: Namespace._from_type(cls, name=__namespace)  # type: ignore[return-value]
        return Namespace._from_type(__namespace)

    @staticmethod
    def auto(
        default: MaybeMissing[MaybeEvaluatable[A]] = MISSING,
        doc: str = "",
        type: Type[T] = cast(Type, Any),
        domain: MaybeMissing[MaybeEvaluatable[_Domain]] = MISSING,
    ) -> "Option[T]":
        """Create an option in a namespace with an inferred key

        Sometimes when creating a namespace, we want to add an option with a docstring or some
        additional transformations, but we want the key to be inferred from the namespace. This
        function creates an option with a default value and docstring, but automatically infers
        the key.

        Example Usage
        -------------
        >>> from labrea import Option
        >>> @Option.namespace
        ... class MY_PACKAGE:
        ...     A = Option.auto(default='foo', doc='An automatic option') >> str
        ...
        >>> print(MY_PACKAGE.__doc__)
        Namespace MY_PACKAGE:
            Option MY_PACKAGE.A (default 'foo'): An automatic option
        >>> MY_PACKAGE.A()
        'foo'
        >>> MY_PACKAGE.A({'MY_PACKAGE': {'A': 100}})
        '100'  # str transformation applied
        """
        return _Auto(default, doc, type, domain)  # type: ignore

    def set(self, options: Options, value: JSON) -> Options:
        """Set the value of the option in the options dictionary.

        Arguments
        ----------
        options : Options
            The options dictionary to modify.
        value : A
            The value to set the option to.

        Returns
        -------
        Options
            The modified options dictionary


        Example Usage
        -------------
        >>> from labrea import Option
        >>> o = Option('A.Y')
        >>> o.set({'A': {'X': 'foo'}}, 'bar')
        {'A': {'X': 'foo', 'Y': 'bar'}}
        """
        new: Dict[str, JSON] = {}
        set_dotted_key(self.key, value, new)
        return mix(options, new)  # type: ignore


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
        try:
            return resolve(options)
        except KeyError as e:
            raise KeyNotFoundError(e.args[0], self) from e

    def validate(self, options: Options) -> None:
        _ = self.evaluate(options)

    def keys(self, options: Options) -> Set[str]:
        return set(options.keys())

    def explain(self, options: Optional[Options] = None) -> Set[str]:
        return set() if options is None else set(options.keys())

    def __repr__(self) -> str:
        return "AllOptions"


AllOptions = _AllOptions()
AllOptions.__doc__ = """An object that evaluates to the entire options dictionary."""


class UnrecognizedNamespaceMemberWarning(Warning):
    """Error raised when a passed option is not recognized in a namespace."""


class Namespace(Evaluatable[Options]):
    """Namespace for options that allows for better documentation and organization.

    This class should probably not be used directly. Instead, use the :meth:`Option.namespace`
    decorator.
    """

    _key: str
    _full: Option
    _members: Mapping[str, Union[Option, "_Auto", "Namespace"]]
    __doc__: str

    def __init__(
        self, key: str, members: Mapping[str, Union[Option, "_Auto", "Namespace"]]
    ) -> None:
        self._key = key
        self._full = Option(key, default={})
        self._members = members
        self.__doc__ = self._build_doc()

    def evaluate(self, options: Options) -> Options:
        return get_dotted_key(self._key, self._populate({}, options))

    def validate(self, options: Options) -> None:
        for name in self._members:
            self[name].validate(options)

        section = Option[Options](self._key, {})(options)
        for name in section:
            if name not in self._members:
                warnings.warn(
                    f"Unrecognized option {name!r} in namespace {self._key}",
                    UnrecognizedNamespaceMemberWarning,
                )

    def keys(self, options: Options) -> Set[str]:
        return set().union(*(self[name].keys(options) for name in self._members))

    def explain(self, options: Optional[Options] = None) -> Set[str]:
        return set().union(*(self[name].explain(options) for name in self._members))

    def __getitem__(self, key: str) -> Evaluatable:
        item = self._members[key]
        if isinstance(item, _Auto):
            return item.build(f"{self._key}.{key}")
        return item

    def __getattr__(self, key: str) -> Evaluatable:
        try:
            return self[key]
        except KeyError:
            raise AttributeError(f"Namespace {self._key} has no attribute {key!r}")

    def __repr__(self) -> str:
        return f"Namespace({self._key!r})"

    def _populate(self, result: Options, options: Options) -> Options:
        for name in self._members:
            member = self[name]
            if isinstance(member, Namespace):
                result = member._populate(result, options)
            elif isinstance(member, Option):
                result = member.set(result, member(options))

        return result

    @staticmethod
    def _build_doc_option(option: Option) -> str:
        doc = f"Option {option.key}"
        if option.default is not MISSING:
            default = (
                option.default.value
                if isinstance(option.default, Value)
                else option.default.template
                if isinstance(option.default, Template)
                else option.default
            )
            doc += f" (default {default!r})"
        if option.__doc__:
            doc += ": " + "\n  ".join(option.__doc__.strip().splitlines())
        return doc

    def _build_doc(self) -> str:
        members = sorted(self._members.items(), key=lambda x: x[0])
        options: List[Option] = []
        namespaces: List[Namespace] = []

        for name, value in members:
            if name.startswith("_"):
                continue
            if isinstance(value, Namespace):
                namespaces.append(value)
            elif isinstance(value, Option):
                options.append(value)
            elif isinstance(value, _Auto):
                options.append(value.option(f"{self._key}.{name}"))

        header = f"Namespace {self._key}:\n  "
        option_docs = (
            "\n  ".join(self._build_doc_option(opt).splitlines()) for opt in options
        )
        namespace_docs = (
            "\n  ".join((ns.__doc__ or "").splitlines()) + "\n" for ns in namespaces
        )

        return header + "\n  ".join((*option_docs, *namespace_docs)).rstrip()

    @classmethod
    def _from_type(
        cls, __namespace: Type, parent: Optional[str] = None, name: Optional[str] = None
    ) -> "Namespace":
        name = name or __namespace.__name__
        key = f"{parent}.{name}" if parent else name

        members: Dict[str, Union[Option, _Auto, Namespace]] = {}
        for name_, type_ in getattr(__namespace, "__annotations__", {}).items():
            members[name_] = Option(f"{key}.{name_}", type=type_)

        for name_, value in __namespace.__dict__.items():
            if isinstance(value, Namespace):
                members[name_] = value._inherit(key)
            elif isinstance(value, Option):
                if "." in value.key:
                    raise ValueError(
                        f"Namespace {key} has nested option {name_}: {value.key}"
                    )
                members[name_] = Option(
                    f"{key}.{value.key}",
                    default=value.default,
                    doc=value.__doc__ or "",
                    type=value.type,
                )
            elif isinstance(value, _Auto):
                members[name_] = value
            elif name_.startswith("_"):
                continue
            elif isinstance(value, type):
                members[name_] = cls._from_type(value, parent=key)
            elif value is None or isinstance(
                value, (str, int, float, bool, list, dict, Evaluatable)
            ):
                members[name_] = Option(f"{key}.{name_}", default=value)
            else:
                raise TypeError(
                    f"Namespace {key} has non-JSON-serializable default value {name_}: {value!r}"
                )

        return cls(key, members)

    def _inherit(self, parent: str) -> "Namespace":
        return Namespace(
            f"{parent}.{self._key}",
            {
                name: (
                    value._inherit(parent)
                    if isinstance(value, Namespace)
                    else Option(
                        f"{parent}.{value.key}", value.default, doc=value.__doc__ or ""
                    )
                    if isinstance(value, Option)
                    else value
                )
                for name, value in self._members.items()
            },
        )


class _Auto(Generic[A]):
    default: MaybeMissing[MaybeEvaluatable[A]]
    doc: str
    type: Type[A]
    domain: MaybeMissing[MaybeEvaluatable[_Domain]]
    transformations: List[Callable]

    def __init__(
        self,
        default: MaybeMissing[MaybeEvaluatable[A]] = MISSING,
        doc: str = "",
        type: Type[A] = cast(Type, Any),
        domain: MaybeMissing[MaybeEvaluatable[_Domain]] = MISSING,
        *transformations: Callable,
    ) -> None:
        self.default = default
        self.doc = doc
        self.type = type
        self.domain = domain
        self.transformations = list(transformations)

    def option(self, key: str) -> Option[A]:
        return Option(
            key, self.default, doc=self.doc, type=self.type, domain=self.domain
        )

    def build(self, key: str, bare: bool = False) -> Evaluatable[A]:
        option: Evaluatable = self.option(key)

        for tform in self.transformations:
            option = option >> tform

        option.__doc__ = self.doc or option.__doc__

        return option

    def __rshift__(self, func: MaybeEvaluatable[Callable[[A], B]]) -> Evaluatable[B]:
        return _Auto(  # type: ignore
            self.default, self.doc, self.type, self.domain, *self.transformations, func
        )
