from typing import Optional, Set, TypeVar, cast
import os

from .coalesce import Coalesce
from .exceptions import EvaluationError
from .types import MaybeEvaluatable, Evaluatable, Options


T = TypeVar("T")


class EnvVar(Evaluatable[str]):
    key: str

    def __init__(self, key: str) -> None:
        self.key = key

    def evaluate(self, options: Options) -> str:
        try:
            return os.environ[self.key]
        except KeyError as e:
            raise EvaluationError(f"Environment variable '{self.key}' not found", self) from e

    def validate(self, options: Options) -> None:
        if self.key not in os.environ:
            raise EvaluationError(f"Environment variable '{self.key}' not found", self)

    def keys(self, options: Options) -> Set[str]:
        return set()

    def explain(self, options: Optional[Options] = None) -> Set[str]:
        return set()

    def __repr__(self) -> str:
        return f"ENV.{self.key}"

    def __or__(self, other: MaybeEvaluatable[T]) -> Evaluatable[T | str]:
        other = cast(Evaluatable[T], other)
        return Coalesce(self, Evaluatable.ensure(other))


class _EnvFactory:
    def __getattr__(self, item: str) -> EnvVar:
        return EnvVar(item)


ENV = _EnvFactory()
