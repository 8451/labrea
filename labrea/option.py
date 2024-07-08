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
    evaluatable: Evaluatable[B]
    options: Options

    def __init__(self, evaluatable: Evaluatable[B], options: Options) -> None:
        self.evaluatable = evaluatable
        self.options = options

    def _options(self, options: Options) -> Options:
        return mix(options, self.options)  # type: ignore

    def evaluate(self, options: Options) -> B:
        return self.evaluatable.evaluate(self._options(options))

    def validate(self, options: Options) -> None:
        self.evaluatable.validate(self._options(options))

    def keys(self, options: Options) -> Set[str]:
        return {
            key
            for key in self.evaluatable.keys(self._options(options))
            if not dotted_key_exists(key, self.options)
        }

    def explain(self, options: Optional[Options] = None) -> Set[str]:
        return {
            key
            for key in self.evaluatable.explain(self._options(options or {}))
            if not dotted_key_exists(key, self.options)
        }

    def __repr__(self) -> str:
        return f"WithOptions({self.evaluatable!r}, {self.options!r})"
