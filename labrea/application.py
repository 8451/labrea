from typing import Callable, Generic, ParamSpec, Set, TypeVar

from .arguments import Arguments, arguments
from .evaluatable import Evaluatable, Options

P = ParamSpec("P")
A = TypeVar("A", covariant=True)


class Application(Generic[P, A], Evaluatable[A]):
    """A class representing the application of a function to a set of arguments."""

    func: Callable[P, A]
    arguments: Evaluatable[Arguments[P]]
    _repr: str

    def __init__(
        self,
        __func: Callable[P, A],
        /,
        *args: Evaluatable[P.args],
        **kwargs: Evaluatable[P.kwargs],
    ):
        self.func = __func
        self.arguments = arguments(*args, **kwargs)

        self._repr = (
            f"Application("
            f"{', '.join(map(repr, args))}"
            f"{', '.join(f'{key}={value!r}' for key, value in kwargs.items())}"
            f")"
        )

    def evaluate(self, options: Options) -> A:
        args = self.arguments.evaluate(options)
        return self.func(*args.args, **args.kwargs)

    def validate(self, options: Options) -> None:
        self.arguments.validate(options)

    def keys(self, options: Options) -> Set[str]:
        return self.arguments.keys(options)

    def __repr__(self) -> str:
        return self._repr
