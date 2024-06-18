import inspect
from typing import (
    Callable,
    Dict,
    Generic,
    Optional,
    ParamSpec,
    Set,
    TypeVar,
    Union,
    overload,
)

from .arguments import Arguments, arguments
from .evaluatable import Evaluatable, MaybeEvaluatable, Options

P = ParamSpec("P")
A = TypeVar("A", covariant=True)


class FunctionApplication(Generic[P, A], Evaluatable[A]):
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
            f"FunctionApplication("
            f"{self.func.__name__}, "
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

    def explain(self, options: Optional[Options] = None) -> Set[str]:
        return self.arguments.explain(options)

    def __repr__(self) -> str:
        return self._repr

    @overload
    @classmethod
    def lift(
        cls,
        __func: Callable[P, A],
        /,
        **kwargs: "MaybeEvaluatable[P.kwargs]",
    ) -> "FunctionApplication[P, A]":
        ...

    @overload
    @classmethod
    def lift(
        cls,
        __func: None = None,
        /,
        **kwargs: "MaybeEvaluatable[P.kwargs]",
    ) -> Callable[[Callable[P, A]], "FunctionApplication[P, A]"]:
        ...

    @classmethod
    def lift(
        cls,
        __func: Optional[Callable[P, A]] = None,
        /,
        **kwargs: "MaybeEvaluatable[P.kwargs]",
    ) -> Union[
        "FunctionApplication[P, A]",
        Callable[[Callable[P, A]], "FunctionApplication[P, A]"],
    ]:
        if __func is None:
            return lambda f: cls.lift(f, **kwargs)

        signature = inspect.signature(__func)
        eval_kwargs: Dict[str, Evaluatable["P.kwargs"]] = {}

        for param in signature.parameters.values():
            if param.default is param.empty:
                raise TypeError(
                    f"Cannot lift function {__func} with non-defaulted parameters"
                )
            eval_kwargs[param.name] = Evaluatable.ensure(param.default)

        return FunctionApplication(__func, **eval_kwargs)
