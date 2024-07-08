import sys

if sys.version_info < (3, 10):
    from typing_extensions import Concatenate, ParamSpec
else:
    from typing import Concatenate, ParamSpec

import inspect
from typing import Callable, Dict, Generic, Optional, Set, TypeVar, Union, overload

from .arguments import Arguments, arguments
from .types import Evaluatable, MaybeEvaluatable, Options

P = ParamSpec("P")
A = TypeVar("A", covariant=True)
X = TypeVar("X")


class FunctionApplication(Generic[P, A], Evaluatable[A]):
    """A class representing the application of a function to a set of arguments."""

    func: Callable[P, A]
    arguments: Evaluatable[Arguments[P]]
    _repr: str

    def __init__(
        self,
        __func: Callable[P, A],
        /,
        *args: "MaybeEvaluatable[P.args]",
        **kwargs: "MaybeEvaluatable[P.kwargs]",
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
        ...  # pragma: no cover

    @overload
    @classmethod
    def lift(
        cls,
        __func: None = None,
        /,
        **kwargs: "MaybeEvaluatable[P.kwargs]",
    ) -> Callable[[Callable[P, A]], "FunctionApplication[P, A]"]:
        ...  # pragma: no cover

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
            default = kwargs.get(param.name, param.default)
            if default is param.empty:
                raise TypeError(
                    f"Cannot lift function {__func} with non-defaulted parameters"
                )
            eval_kwargs[param.name] = Evaluatable.ensure(default)

        return FunctionApplication(__func, **eval_kwargs)


class PartialApplication(Generic[X, P, A], Evaluatable[Callable[[X], A]]):
    func: Callable[Concatenate[X, P], A]
    arguments: Evaluatable[Arguments[P]]
    _repr: str

    def __init__(
        self,
        __func: Callable[Concatenate[X, P], A],
        /,
        *args: Evaluatable["P.args"],
        **kwargs: Evaluatable["P.kwargs"],
    ):
        self.func = __func
        self.arguments = arguments(*args, **kwargs)

        self._repr = (
            f"PartialApplication("
            f"{self.func.__name__}, "
            f"{', '.join(map(repr, args))}"
            f"{', '.join(f'{key}={value!r}' for key, value in kwargs.items())}"
            f")"
        )

    def evaluate(self, options: Options) -> Callable[[X], A]:
        args = self.arguments.evaluate(options)
        return lambda x: self.func(x, *args.args, **args.kwargs)

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
        __func: Callable[Concatenate[X, P], A],
        /,
        **kwargs: "MaybeEvaluatable[P.kwargs]",
    ) -> "PartialApplication[X, P, A]":
        ...  # pragma: no cover

    @overload
    @classmethod
    def lift(
        cls,
        __func: None = None,
        /,
        **kwargs: "MaybeEvaluatable[P.kwargs]",
    ) -> Callable[[Callable[Concatenate[X, P], A]], "PartialApplication[X, P, A]"]:
        ...  # pragma: no cover

    @classmethod
    def lift(
        cls,
        __func: Optional[Callable[Concatenate[X, P], A]] = None,
        /,
        **kwargs: "MaybeEvaluatable[P.kwargs]",
    ) -> Union[
        "PartialApplication[X, P, A]",
        Callable[[Callable[Concatenate[X, P], A]], "PartialApplication[X, P, A]"],
    ]:
        if __func is None:
            return lambda f: cls.lift(f, **kwargs)

        signature = inspect.signature(__func)
        eval_kwargs: Dict[str, Evaluatable["P.kwargs"]] = {}

        for i, param in enumerate(signature.parameters.values()):
            default = kwargs.get(param.name, param.default)
            if i == 0 and default is not param.empty:
                raise TypeError(
                    f"Cannot create a PartialApplication with a default value "
                    f"for the first parameter of {__func}"
                )
            elif i > 0 and default is param.empty:
                raise TypeError(
                    f"Cannot lift function {__func} with non-defaulted parameters "
                    f"after the first parameter"
                )
            elif default is not param.empty:
                eval_kwargs[param.name] = Evaluatable.ensure(default)

        return PartialApplication(__func, **eval_kwargs)
