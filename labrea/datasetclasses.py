import functools
import operator
from types import new_class
from typing import Any, Generic, Set, Type, TypeVar

from .types import Evaluatable, JSONDict, Value

A = TypeVar("A")


class DatasetClassMeta(type, Generic[A]):
    def __init__(cls, *args, **kwargs):
        annotations = functools.reduce(
            operator.or_,
            (
                getattr(base, "__annotations__", {})
                for base in reversed(cls.__bases__)
                if base is not DatasetClass
            ),
        )

        for key in annotations.keys():
            try:
                val = getattr(cls, key)
            except AttributeError:
                raise AttributeError(
                    f"Annotation {key} on class {cls.__name__} has "
                    f"no default value."
                )

            if not isinstance(val, Evaluatable):
                setattr(cls, key, Field(val))

        super().__init__(*args, **kwargs)

    def evaluate(cls, options: JSONDict) -> A:
        return cls(options)

    def validate(cls, options: JSONDict) -> None:
        for key in dir(cls):
            dependency = getattr(cls, key, None)
            if isinstance(dependency, Evaluatable) and not key.startswith("__"):
                dependency.validate(options)

    def keys(cls, options: JSONDict) -> Set[str]:
        return {
            key
            for name in dir(cls)
            if (
                isinstance(getattr(cls, name), Evaluatable)
                and not name.startswith("__")
            )
            for key in getattr(cls, name).keys(options)
        }

    @property
    def result(cls) -> A:
        return cls  # type: ignore


class Field(Value):
    """A wrapper for a static value.

    This is an alias for :class:`labrea.types.Value`.
    """

    pass


class DatasetClass:
    def __init__(self, options: JSONDict):
        key: str
        val: Any
        for key in dir(self.__class__):
            val = getattr(self, key)
            if isinstance(val, Evaluatable) and not key.startswith("__"):
                setattr(self, key, val.evaluate(options))


def datasetclass(c: Type[A]) -> DatasetClassMeta[A]:
    """Create a new DatasetClass from a class definition.

    DatasetClasses are classes that when instatiated, evaluate their
    members using the options dict provided to the constructor. This
    allows for the definition of complex data structures that can be
    evaluated at runtime.

    Any members of the class that are not Evaluatables are wrapped in
    :class:`labrea.datasetclasses.Field` instances.

    Example Usage
    -------------
    >>> from labrea import dataset, datasetclass, Option
    >>> @dataset
    ... def my_dataset(a: str = Option('A')) -> str:
    ...     return a
    >>>
    >>> @datasetclass
    ... class MyDatasetClass:
    ...     a: str = my_dataset
    ...     b: int = Option('B')
    ...     c: bool = True
    ...
    >>> inst = MyDatasetClass({'A': 'Hello World!', 'B': 1})
    >>> print(inst.a, inst.b, inst.c)  # Hello World! 1 True
    """
    dataset_class = new_class(
        c.__name__, (c, DatasetClass), kwds={"metaclass": DatasetClassMeta}
    )

    functools.update_wrapper(dataset_class, c, updated=())

    return dataset_class  # type: ignore
