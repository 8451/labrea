from typing import Optional, Set, TypeVar

from confectioner.templating import dotted_key_exists, get_dotted_key, resolve

from ._missing import MISSING, MaybeMissing
from .evaluatable import Evaluatable, KeyNotFoundError, MaybeEvaluatable, Options
from .template import Template
from .types import JSON

A = TypeVar("A", covariant=True, bound=JSON)


class Option(Evaluatable[A]):
    key: str
    default: MaybeMissing[Evaluatable[A]]

    def __init__(
        self,
        key: str,
        default: MaybeMissing[MaybeEvaluatable[A]] = MISSING,
        doc: str = "",
    ) -> None:
        self.key = key
        if default is MISSING:
            self.default = default
        elif isinstance(default, str):
            self.default = Template(default)  # type: ignore [assignment]
        else:
            self.default = Evaluatable.ensure(default)

        self.__doc__ = doc

    def evaluate(self, options: Options) -> A:
        """Retrieves the value from the options dictionary.

        If the key does not exist, the default value is returned. If no default
        value is provided, an error is raised. If the default value is an
        Evaluatable, it is evaluated using the options dictionary. If the
        default value is not an Evaluatable, it is returned as-is.
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

        If the key does not exist, the default value is validated. If the
        default value is an Evaluatable, it is validated using the options
        dictionary. If the default value is not an Evaluatable, it is ignored.
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
