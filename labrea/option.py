import builtins
from typing import Set, TypeVar, Union

from confectioner.templating import dotted_key_exists, get_dotted_key, resolve

from .evaluatable import Evaluatable, MaybeEvaluatable, Options
from .template import Template

A = TypeVar("A")


class Option(Evaluatable[A]):
    key: str
    default: Union[Evaluatable[A], builtins.ellipsis]

    def __init__(
        self,
        key: str,
        default: Union[MaybeEvaluatable[A], builtins.ellipsis] = ...,
        doc: str = "",
    ) -> None:
        self.key = key
        if default is ...:
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
            if self.default is ...:
                self.panic(self.key)
            return self.default.evaluate(options)

    def validate(self, options: Options) -> None:
        """Validates that the key exists in the options dictionary.

        If the key does not exist, the default value is validated. If the
        default value is an Evaluatable, it is validated using the options
        dictionary. If the default value is not an Evaluatable, it is ignored.
        """
        if not dotted_key_exists(self.key, options):
            if self.default is ...:
                self.panic(self.key)
            self.default.validate(options)

    def keys(self, options: Options) -> Set[str]:
        return {self.key} | (
            set() if self.default is ... else self.default.keys(options)
        )

    @property
    def has_default(self) -> bool:
        return self.default is not ...

    def __repr__(self) -> str:
        return (
            f"Option({self.key!r}, default={self.default!r})"
            if self.has_default
            else f"Option({self.key!r})"
        )
