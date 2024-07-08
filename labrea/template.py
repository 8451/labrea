import re
import warnings
from typing import Any, Dict, Optional, Set

from confectioner import mix
from confectioner.templating import find_template_keys, resolve

from .exceptions import KeyNotFoundError
from .types import Evaluatable, Options, Value

TEMPLATE_PARAM = re.compile(r"^:[a-zA-Z_][a-zA-Z0-9_]*:$")


class Template(Evaluatable[str]):
    """A template string that can be evaluated using other Evaluatables.

    Template entries use the format :code:`{:key:}` where :code:`key` is the
    name of a parameter (keyword argument). The parameter can be any
    Evaluatable. The template is evaluated using the options dictionary and
    the result is returned as a string. Normal options can also be used in
    the template using the standard :code:`{NESTED.KEY}` syntax from
    confectioner.

    Arguments
    ----------
    template : str
        The template string to evaluate
    kwargs : Any
        The parameters to use when evaluating the template. Each parameter
        can be any Evaluatable. If a parameter is not an Evaluatable, it is
        used as a constant key.

    Raises
    ------
    ValueError
        If the template requires parameters that are not provided


    Example Usage
    -------------
    >>> from labrea import Template, dataset, Option
    >>> @dataset
    ... def b_dataset(b: str = Option('V')) -> str:
    ...     return b
    >>>
    >>> t = Template('{A.X} {:b:}', b=b_dataset)
    >>> t({'A': {'X': 'Hello'}, 'V': 'World!'})  # 'Hello World!'

    """

    template: str
    params: Dict[str, Evaluatable[Any]]

    def __init__(self, template: str, **kwargs):
        self.template = template
        self.params = {
            key: value if isinstance(value, Evaluatable) else Value(value)
            for key, value in kwargs.items()
        }

        required_params = {
            key[1:-1]
            for key in find_template_keys(template)
            if TEMPLATE_PARAM.match(key)
        }

        missing_params = required_params - self.params.keys()
        if missing_params:
            raise ValueError(
                f"Template {template} requires parameters "
                f'{",".join(required_params)}'
            )

        extra_params = set(self.params.keys()) - required_params
        if extra_params:
            warnings.warn(
                f'Unused parameters {",".join(extra_params)} for template '
                f"{template}"
            )

    def evaluate(self, options: Options) -> str:
        """Evaluates the template using the options dictionary."""
        params = {f":{key}:": val.evaluate(options) for key, val in self.params.items()}

        try:
            return str(resolve(self.template, mix(options, params)))  # type: ignore
        except KeyError as e:
            raise KeyNotFoundError((*e.args, "UNKNOWN")[0], self) from e

    def validate(self, options: Options) -> None:
        """Validates that the template can be evaluated using the options."""
        from .option import Option

        for val in self.params.values():
            val.validate(options)

        for key in find_template_keys(self.template):
            if TEMPLATE_PARAM.match(key):
                continue
            try:
                Option(key).validate(options)
            except KeyNotFoundError as e:
                raise KeyNotFoundError(e.key, self) from e

    def keys(self, options: Options) -> Set[str]:
        """Returns the keys that this object depends on."""
        from .option import Option

        keys = set().union(*(value.keys(options) for value in self.params.values()))
        for key in find_template_keys(self.template):
            if TEMPLATE_PARAM.match(key):
                continue
            try:
                keys.update(Option(key).keys(options))
            except KeyNotFoundError as e:
                raise KeyNotFoundError(e.key, self) from e

        return keys

    def explain(self, options: Optional[Options] = None) -> Set[str]:
        """Returns the keys that this object depends on."""
        from .option import Option

        options = options or {}
        keys = set().union(*(value.explain(options) for value in self.params.values()))
        for key in find_template_keys(self.template):
            if TEMPLATE_PARAM.match(key):
                continue

            keys.update(Option(key).explain(options))

        return keys

    def __repr__(self) -> str:
        if self.params:
            return (
                f"Template({self.template!r}, "
                f"{', '.join(f'{key}={value!r}' for key, value in self.params.items())}"
                f")"
            )

        return f"Template({self.template!r})"
