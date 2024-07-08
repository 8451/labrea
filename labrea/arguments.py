import sys

if sys.version_info < (3, 10):
    from typing_extensions import ParamSpec
else:
    from typing import ParamSpec

from typing import Dict, Generic, Optional, Set, Tuple

from .types import Evaluatable, MaybeEvaluatable, Options

P = ParamSpec("P")


class Arguments(Generic[P]):
    """A class representing the arguments of a function or method."""

    args: P.args
    kwargs: P.kwargs

    def __init__(self, *args: P.args, **kwargs: P.kwargs):
        self.args = args
        self.kwargs = kwargs

    def __repr__(self) -> str:
        args_repr = ", ".join(map(repr, self.args))
        kwargs_repr = ", ".join(
            f"{key}={value!r}" for key, value in self.kwargs.items()
        )
        return f"Arguments({', '.join(filter(bool, [args_repr, kwargs_repr]))})"

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Arguments):
            return NotImplemented
        return self.args == other.args and self.kwargs == other.kwargs


class EvaluatableArgs(Generic[P], Evaluatable["P.args"]):
    """A class representing a set of arguments that can be evaluated."""

    args: Tuple[Evaluatable, ...]

    def __init__(self, *args: Evaluatable["P.args"]):
        self.args = args

    def evaluate(self, options: Options) -> "P.args":
        return tuple(arg.evaluate(options) for arg in self.args)  # type: ignore

    def validate(self, options: Options) -> None:
        for arg in self.args:
            arg.validate(options)

    def keys(self, options: Options) -> Set[str]:
        return set().union(*(arg.keys(options) for arg in self.args))

    def explain(self, options: Optional[Options] = None) -> Set[str]:
        return set().union(*(arg.explain(options) for arg in self.args))

    def __repr__(self) -> str:
        return f"EvaluatableArgs({', '.join(map(repr, self.args))})"


class EvaluatableKwargs(Generic[P], Evaluatable["P.kwargs"]):
    """A class representing a set of keyword arguments that can be evaluated."""

    kwargs: Dict[str, Evaluatable]

    def __init__(self, **kwargs: Evaluatable["P.kwargs"]):
        self.kwargs = kwargs

    def evaluate(self, options: Options) -> "P.kwargs":
        return {key: value.evaluate(options) for key, value in self.kwargs.items()}  # type: ignore

    def validate(self, options: Options) -> None:
        for value in self.kwargs.values():
            value.validate(options)

    def keys(self, options: Options) -> Set[str]:
        return set().union(*(value.keys(options) for value in self.kwargs.values()))

    def explain(self, options: Optional[Options] = None) -> Set[str]:
        return set().union(*(value.explain(options) for value in self.kwargs.values()))

    def __repr__(self) -> str:
        return (
            f"EvaluatableKwargs("
            f"{', '.join(f'{key}={value!r}' for key, value in self.kwargs.items())}"
            f")"
        )


class EvaluatableArguments(Evaluatable[Arguments[P]]):
    """A class representing a set of arguments that can be evaluated."""

    args: EvaluatableArgs[P]
    kwargs: EvaluatableKwargs[P]

    def __init__(self, *args: Evaluatable["P.args"], **kwargs: Evaluatable["P.kwargs"]):
        self.args = EvaluatableArgs(*args)
        self.kwargs = EvaluatableKwargs(**kwargs)

    def evaluate(self, options: Options) -> Arguments[P]:
        return Arguments(*self.args.evaluate(options), **self.kwargs.evaluate(options))

    def validate(self, options: Options) -> None:
        self.args.validate(options)
        self.kwargs.validate(options)

    def keys(self, options: Options) -> Set[str]:
        return self.args.keys(options).union(self.kwargs.keys(options))

    def explain(self, options: Optional[Options] = None) -> Set[str]:
        return self.args.explain(options) | self.kwargs.explain(options)

    def __repr__(self) -> str:
        return (
            f"EvaluatableParameters("
            f"{', '.join(map(repr, self.args.args))}, "
            f"{', '.join(f'{key}={value!r}' for key, value in self.kwargs.kwargs.items())}"
            f")"
        )


def arguments(
    *args: MaybeEvaluatable["P.args"], **kwargs: MaybeEvaluatable["P.kwargs"]
) -> Evaluatable[Arguments[P]]:
    return EvaluatableArguments(
        *(Evaluatable.ensure(arg) for arg in args),
        **{key: Evaluatable.ensure(value) for key, value in kwargs.items()},
    )
