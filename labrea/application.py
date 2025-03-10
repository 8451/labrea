import sys

if sys.version_info < (3, 10):
    from typing_extensions import ParamSpec
else:
    from typing import ParamSpec

import functools
import inspect
from typing import Callable, Dict, Generic, Optional, Set, TypeVar, Union, overload

from .arguments import Arguments, arguments
from .types import Evaluatable, MaybeEvaluatable, Options

P = ParamSpec("P")
A = TypeVar("A", covariant=True)
X = TypeVar("X")


class FunctionApplication(Generic[P, A], Evaluatable[A]):
    """A class representing the application of a function to a set of arguments.

    This class is what is used by the :class:`labrea.dataset.Dataset` under the hood.

    Arguments
    ---------
    __func : Callable[P, A]
        The function to apply.
    *args : MaybeEvaluatable[P.args]
        The positional arguments to evaluate.
    **kwargs : MaybeEvaluatable[P.kwargs]
        The keyword arguments to evaluate.
    """

    func: Evaluatable[Callable[P, A]]
    arguments: Evaluatable[Arguments[P]]
    _repr: str

    def __init__(
        self,
        __func: MaybeEvaluatable[Callable[P, A]],
        /,
        *args: "MaybeEvaluatable[P.args]",
        **kwargs: "MaybeEvaluatable[P.kwargs]",
    ):
        self.func = Evaluatable.ensure(__func)
        self.arguments = arguments(*args, **kwargs)

        self._repr = (
            f"FunctionApplication("
            f"{getattr(__func, '__name__', repr(__func))}, "
            f"{', '.join(map(repr, args))}"
            f"{', '.join(f'{key}={value!r}' for key, value in kwargs.items())}"
            f")"
        )

    def evaluate(self, options: Options) -> A:
        func = self.func.evaluate(options)
        args = self.arguments.evaluate(options)
        return func(*args.args, **args.kwargs)

    def validate(self, options: Options) -> None:
        self.func.validate(options)
        self.arguments.validate(options)

    def keys(self, options: Options) -> Set[str]:
        return self.func.keys(options) | self.arguments.keys(options)

    def explain(self, options: Optional[Options] = None) -> Set[str]:
        return self.func.explain(options) | self.arguments.explain(options)

    def __repr__(self) -> str:
        return self._repr

    @overload
    @classmethod
    def lift(
        cls,
        __func: Callable[P, A],
        /,
        **kwargs: "MaybeEvaluatable[P.kwargs]",
    ) -> "FunctionApplication[P, A]": ...  # pragma: no cover

    @overload
    @classmethod
    def lift(
        cls,
        __func: None = None,
        /,
        **kwargs: "MaybeEvaluatable[P.kwargs]",
    ) -> Callable[
        [Callable[P, A]], "FunctionApplication[P, A]"
    ]: ...  # pragma: no cover

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
        """Lift a function definition with Evaluatable default arguments to a FunctionApplication.

        This is used by the :func:`labrea.dataset` decorator under the hood. Can be used
        as a decorator with or without keyword arguments for the defaults.

        Arguments
        ---------
        __func : Callable[P, A]
            The function to apply.
        **kwargs : MaybeEvaluatable[P.kwargs]
            Default values for the keyword arguments of the function.

        Returns
        -------
        FunctionApplication[P, A]
            The lifted function application.


        Example Usage
        -------------
        >>> @FunctionApplication.lift
        ... def a_squared(a: int = Option('A')) -> int:
        ...     return a ** 2
        >>>
        >>> @FunctionApplication(a=Option('A'))
        ... def a_squared(a: int) -> int:
        ...     return a ** 2
        >>>
        >>> a_squared = FunctionApplication.lift(lambda a: a**2, a=Option('A'))
        """
        if __func is None:
            return lambda f: cls.lift(f, **kwargs)

        signature = inspect.signature(__func)
        eval_kwargs: Dict[str, Evaluatable["P.kwargs"]] = {}

        has_kwargs = any(
            param.kind == param.VAR_KEYWORD for param in signature.parameters.values()
        )

        for param in signature.parameters.values():
            default = kwargs.get(param.name, param.default)
            if param.kind == param.VAR_KEYWORD:
                continue
            elif default is param.empty:
                raise TypeError(
                    f"Cannot lift function {__func} with non-defaulted parameters"
                )
            eval_kwargs[param.name] = Evaluatable.ensure(default)

        if has_kwargs:
            for key, value in kwargs.items():
                if key not in eval_kwargs:
                    eval_kwargs[key] = Evaluatable.ensure(value)

        return FunctionApplication(__func, **eval_kwargs)


class PartialApplication(Generic[P, A], Evaluatable[Callable[..., A]]):
    """A class representing the partial application of a function to a set of arguments.

    This class is used by the :func:`labrea.pipeline_step` decorator under the hood.

    Arguments
    ---------
    __func : Callable[P, A]
        The function to apply.
    *args : MaybeEvaluatable[P.args]
        The positional arguments to evaluate.
    **kwargs : MaybeEvaluatable[P.kwargs]
        The keyword arguments to evaluate.
    """

    func: Evaluatable[Callable[P, A]]
    arguments: Evaluatable[Arguments[P]]
    _repr: str

    def __init__(
        self,
        __func: MaybeEvaluatable[Callable[P, A]],
        /,
        *args: MaybeEvaluatable["P.args"],
        **kwargs: MaybeEvaluatable["P.kwargs"],
    ):
        self.func = Evaluatable.ensure(__func)
        self.arguments = arguments(*args, **kwargs)

        self._repr = (
            f"PartialApplication("
            f"{getattr(__func, '__name__', repr(__func))}, "
            f"{', '.join(map(repr, args))}"
            f"{', '.join(f'{key}={value!r}' for key, value in kwargs.items())}"
            f")"
        )

    def evaluate(self, options: Options) -> Callable[..., A]:
        func = self.func.evaluate(options)
        args = self.arguments.evaluate(options)
        return functools.partial(func, *args.args, **args.kwargs)

    def validate(self, options: Options) -> None:
        self.func.validate(options)
        self.arguments.validate(options)

    def keys(self, options: Options) -> Set[str]:
        return self.func.keys(options) | self.arguments.keys(options)

    def explain(self, options: Optional[Options] = None) -> Set[str]:
        return self.func.explain(options) | self.arguments.explain(options)

    def __repr__(self) -> str:
        return self._repr

    @overload
    @classmethod
    def lift(
        cls,
        __func: Callable[P, A],
        /,
        **kwargs: "MaybeEvaluatable[P.kwargs]",
    ) -> "PartialApplication[P, A]": ...  # pragma: no cover

    @overload
    @classmethod
    def lift(
        cls,
        __func: None = None,
        /,
        **kwargs: "MaybeEvaluatable[P.kwargs]",
    ) -> Callable[[Callable[P, A]], "PartialApplication[P, A]"]: ...  # pragma: no cover

    @classmethod
    def lift(
        cls,
        __func: Optional[Callable[P, A]] = None,
        /,
        **kwargs: "MaybeEvaluatable[P.kwargs]",
    ) -> Union[
        "PartialApplication[P, A]",
        Callable[[Callable[P, A]], "PartialApplication[P, A]"],
    ]:
        """Lift a function definition with Evaluatable default arguments to a PartialApplication.

        This is used by the :func:`labrea.pipeline_step` decorator under the hood. Can be used
        as a decorator with or without keyword arguments for the defaults.

        Arguments
        ---------
        __func : Callable[P, A]
            The function to apply.
        **kwargs : MaybeEvaluatable[P.kwargs]
            Default values for the keyword arguments of the function.

        Returns
        -------
        PartialApplication[P, A]
            The lifted partial application.


        Example Usage
        -------------
        >>> @PartialApplication.lift
        ... def a_plus_b(a: int, b: int = Option('B')) -> int:
        ...     return a + b
        >>>
        >>> @PartialApplication(b=Option('B'))
        ... def a_plus_b(a: int, b: int) -> int:
        ...     return a + b
        >>>
        >>> a_plus_b = PartialApplication.lift(lambda a, b: a + b, b=Option('B'))
        """
        if __func is None:
            return lambda f: cls.lift(f, **kwargs)

        signature = inspect.signature(__func)
        eval_kwargs: Dict[str, Evaluatable["P.kwargs"]] = {}

        for i, param in enumerate(signature.parameters.values()):
            default = kwargs.get(param.name, param.default)
            if default is not param.empty:
                eval_kwargs[param.name] = Evaluatable.ensure(default)

        return PartialApplication(__func, **eval_kwargs)
