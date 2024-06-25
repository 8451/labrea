import functools
from dataclasses import dataclass, field, fields
from typing import Iterable, Optional, Self, Set, Type, TypeVar

from .evaluatable import Evaluatable
from .types import Options

T = TypeVar("T")
D = TypeVar("D", bound="_DatasetClassMixin")


class _DatasetClassMixin:
    @classmethod
    def _labrea_evaluate(cls, options: Options) -> Self:
        self = cls()
        for key, value in self.__dict__.items():
            if not key.startswith("__") and isinstance(value, Evaluatable):
                setattr(self, key, value.evaluate(options))

        return self

    @classmethod
    def _labrea_validate(cls, options: Options) -> None:
        for fld in cls._labrea_fields():
            fld.validate(options)

    @classmethod
    def _labrea_keys(cls, options: Options) -> Set[str]:
        return set().union(*(fld.keys(options) for fld in cls._labrea_fields()))

    @classmethod
    def _labrea_explain(cls, options: Optional[Options] = None) -> Set[str]:
        return set().union(*(fld.explain(options) for fld in cls._labrea_fields()))

    @classmethod
    def _labrea_fields(cls) -> Iterable[Evaluatable]:
        return (fld.default_factory() for fld in fields(cls))  # type: ignore


class _DatasetClassEvaluatable(Evaluatable[D]):
    datasetclass: Type[D]

    def __init__(self, cls: Type[D]):
        self.datasetclass = cls
        functools.update_wrapper(self, cls, updated=())

    def evaluate(self, options: Options) -> D:
        return self.datasetclass._labrea_evaluate(options)

    def validate(self, options: Options) -> None:
        self.datasetclass._labrea_validate(options)

    def keys(self, options: Options) -> Set[str]:
        return self.datasetclass._labrea_keys(options)

    def explain(self, options: Optional[Options] = None) -> Set[str]:
        return self.datasetclass._labrea_explain(options)

    def __repr__(self):
        return f"<DatasetClass {self.datasetclass.__qualname__}>"


def datasetclass(cls: Type[T]) -> Evaluatable[T]:
    for key in getattr(cls, "__annotations__", {}):
        try:
            default = getattr(cls, key)
        except AttributeError as e:
            raise ValueError(f"Missing default value for field: {key}") from e

        def _default_factory(x):
            return lambda: Evaluatable.ensure(x)

        setattr(cls, key, field(default_factory=_default_factory(default)))

    @dataclass
    class _DatasetClass(_DatasetClassMixin, dataclass(cls)):  # type: ignore
        pass

    functools.update_wrapper(_DatasetClass, cls, updated=())

    return _DatasetClassEvaluatable(_DatasetClass)  # type: ignore
