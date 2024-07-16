import functools
import operator
from types import new_class
from typing import Any, Dict, Optional, Set, Type, TypeVar

from confectioner.templating import set_dotted_key

from .types import Evaluatable, Options, Value

A = TypeVar("A")


class DatasetClassMeta(type, Evaluatable[A]):
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
                raise ValueError(
                    f"Annotation {key} on class {cls.__name__} has "
                    f"no default value."
                )

            if not isinstance(val, Evaluatable):
                setattr(cls, key, Value(val))

        super().__init__(*args, **kwargs)

    def evaluate(cls, options: Options) -> A:
        return cls(options)

    def validate(cls, options: Options) -> None:
        for key in dir(cls):
            dependency = getattr(cls, key, None)
            if isinstance(dependency, Evaluatable) and not key.startswith("__"):
                dependency.validate(options)

    def keys(cls, options: Options) -> Set[str]:
        return {
            key
            for name in dir(cls)
            if (
                isinstance(getattr(cls, name), Evaluatable)
                and not name.startswith("__")
            )
            for key in getattr(cls, name).keys(options)
        }

    def explain(cls, options: Optional[Options] = None) -> Set[str]:
        return {
            key
            for name in dir(cls)
            if (
                isinstance(getattr(cls, name), Evaluatable)
                and not name.startswith("__")
            )
            for key in getattr(cls, name).explain(options)
        }

    def __subclasses__(cls=None):
        return []

    @property
    def result(cls) -> A:
        return cls  # type: ignore

    def __repr__(self):
        return f"<DatasetClass {self.__name__}>"


class DatasetClass:
    _repr_options: Dict[str, Any]

    def __init__(self, options: Optional[Options] = None):
        options = options or {}

        key: str
        val: Any
        for key in dir(self.__class__):
            val = getattr(self, key)
            if isinstance(val, Evaluatable) and not key.startswith("__"):
                setattr(self, key, val.evaluate(options))

        self._repr_options = {}
        for key in sorted(self.__class__.keys(options)):  # type: ignore [attr-defined]
            value = options.get(key)
            set_dotted_key(key, value, self._repr_options)

    def __repr__(self):
        return f"{self.__class__.__name__}({self._repr_options!r})"

    def __eq__(self, other):
        return (
            isinstance(other, self.__class__)
            and self._repr_options == other._repr_options
        )


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
