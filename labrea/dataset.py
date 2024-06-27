import functools
import typing
from collections import OrderedDict
from typing import (
    Callable,
    Dict,
    Generic,
    Hashable,
    List,
    Mapping,
    Optional,
    ParamSpec,
    Set,
    TypeVar,
    Union,
    overload,
)

from ._missing import MISSING, MaybeMissing
from .application import FunctionApplication
from .cache import Cache, MemoryCache, NoCache, cached
from .computation import CallbackEffect, ChainedEffect, Computation, Effect
from .evaluatable import Evaluatable, MaybeEvaluatable, Value
from .option import Option
from .overload import Overloaded
from .types import Options

A = TypeVar("A", covariant=True)
P = ParamSpec("P")
EffectSet = typing.OrderedDict[str, Effect[A, A]]
Callback = Callable[[A, Options], A]


class Dataset(Evaluatable[A]):
    overloads: Overloaded[A]
    effects: EffectSet[A]
    cache: Cache[A]

    def __init__(
        self, overloads: Overloaded[A], effects: EffectSet[A], cache: Cache[A]
    ):
        self.overloads = overloads
        self.effects = effects
        self.cache = cache

    @property
    def _composed(self) -> Evaluatable[A]:
        return cached(
            Computation(
                self.overloads,
                ChainedEffect(*self.effects.values()),
            ),
            self.cache,
        )

    def evaluate(self, options: Options) -> A:
        return self._composed.evaluate(options)

    def validate(self, options: Options) -> None:
        self._composed.validate(options)

    def keys(self, options: Options) -> Set[str]:
        return self._composed.keys(options)

    def explain(self, options: Optional[Options] = None) -> Set[str]:
        return self._composed.explain(options)

    def __repr__(self) -> str:
        kind = "AbstractDataset" if self.overloads.default is MISSING else "Dataset"
        if hasattr(self, "__qualname__"):
            return f"<{kind} {self.__qualname__}>"
        if hasattr(self, "__name__"):
            return f"<{kind} {self.__name__}>"

        return (  # pragma: no cover
            f"Dataset("
            f"{self.overloads!r}, "
            f"{', '.join(map(repr, self.effects))}, "
            f"{self.cache!r})"
        )

    def overload(
        self,
        alias: Union[Hashable, List[Hashable]],
    ) -> Callable[[Callable[P, A]], FunctionApplication[P, A]]:
        return self.overloads.overload(alias)

    def register(self, key: Hashable, value: Evaluatable[A]) -> None:
        self.overloads.register(key, value)

    def set_dispatch(self, dispatch: Evaluatable[Hashable]) -> None:
        self.overloads = Overloaded(
            dispatch,
            self.overloads.lookup.copy(),
            default=self.overloads.default,
        )

    def set_effect(self, name: str, effect: Union[Effect[A, A], Callback[A]]) -> None:
        self.effects = OrderedDict(
            [
                *self.effects.items(),
                (
                    name,
                    effect if isinstance(effect, Effect) else CallbackEffect(effect),
                ),
            ]
        )

    add_effect = set_effect

    def drop_effect(self, name: str) -> None:
        self.effects = OrderedDict(
            [(key, val) for key, val in self.effects.items() if key != name]
        )

    @property
    def default(self) -> MaybeMissing[Evaluatable[A]]:
        return self.overloads.default

    @property
    def is_abstract(self) -> bool:
        return self.overloads.default is MISSING


class DatasetFactory(Generic[A]):
    effects: EffectSet[A]
    cache: Optional[Cache[A]]
    dispatch: Evaluatable[Hashable]
    defaults: Dict[str, Evaluatable[A]]
    abstract: bool

    def __init__(
        self,
        effects: Optional[EffectSet[A]] = None,
        cache: Optional[Cache[A]] = None,
        dispatch: Union[Evaluatable[Hashable], str, None] = None,
        defaults: Optional[Dict[str, MaybeEvaluatable[A]]] = None,
        abstract: bool = False,
    ):
        self.effects = effects or OrderedDict()
        self.cache = cache
        self.defaults = {
            key: Evaluatable.ensure(val) for key, val in (defaults or {}).items()
        }
        self.abstract = abstract

        if dispatch is None:
            self.dispatch = Value(MISSING)
        elif isinstance(dispatch, str):
            self.dispatch = Option(dispatch)
        else:
            self.dispatch = dispatch

    @overload
    def __call__(
        self,
        definition: Callable[..., A],
        /,
        *,
        effects: Optional[Mapping[str, Union[Effect[A, A], Callback[A]]]] = ...,
        cache: Optional[Cache[A]] = ...,
        dispatch: Optional[Union[Evaluatable[Hashable], str]] = ...,
        defaults: Optional[Dict[str, MaybeEvaluatable[A]]] = ...,
        abstract: Optional[bool] = ...,
    ) -> Dataset[A]:
        ...  # pragma: no cover

    @overload
    def __call__(
        self,
        /,
        *,
        effects: Optional[Mapping[str, Union[Effect[A, A], Callback[A]]]] = ...,
        cache: Optional[Cache[A]] = ...,
        dispatch: Optional[Union[Evaluatable[Hashable], str]] = ...,
        defaults: Optional[Dict[str, MaybeEvaluatable[A]]] = ...,
        abstract: Optional[bool] = ...,
    ) -> "DatasetFactory[A]":
        ...  # pragma: no cover

    @overload
    def __call__(
        self,
        definition: None,
        /,
        *,
        effects: Optional[Mapping[str, Union[Effect[A, A], Callback[A]]]] = ...,
        cache: Optional[Cache[A]] = ...,
        dispatch: Optional[Union[Evaluatable[Hashable], str]] = ...,
        defaults: Optional[Dict[str, MaybeEvaluatable[A]]] = ...,
        abstract: Optional[bool] = ...,
    ) -> "DatasetFactory[A]":
        ...  # pragma: no cover

    def __call__(
        self,
        definition: Optional[Callable[..., A]] = None,
        /,
        *,
        effects: Optional[Mapping[str, Union[Effect[A, A], Callback[A]]]] = None,
        cache: Optional[Cache[A]] = None,
        dispatch: Optional[Union[Evaluatable[Hashable], str]] = None,
        defaults: Optional[Dict[str, MaybeEvaluatable[A]]] = None,
        abstract: Optional[bool] = None,
    ) -> Union["DatasetFactory", Dataset[A]]:
        _effects = OrderedDict(
            [
                (key, effect if isinstance(effect, Effect) else CallbackEffect(effect))
                for key, effect in (effects or {}).items()
            ]
        )
        factory = self.update(
            effects=_effects,
            cache=cache,
            dispatch=dispatch,
            defaults=defaults,
            abstract=abstract,
        )

        if definition is not None:
            return factory.wrap(definition)

        return factory

    def wrap(self, definition: Callable[..., A]) -> Dataset[A]:
        overloads: Overloaded[A]
        if not self.abstract:
            lifted = FunctionApplication.lift(definition, **self.defaults)
            overloads = Overloaded(self.dispatch, {}, lifted)
        else:
            if self.dispatch == Value(MISSING):
                raise ValueError("Abstract datasets must have a dispatch")
            overloads = Overloaded(self.dispatch, {})

        _dataset = Dataset(
            overloads, effects=self.effects, cache=self.cache or MemoryCache()
        )

        functools.update_wrapper(_dataset, definition, updated=())

        return _dataset

    def where(self, **defaults: MaybeEvaluatable[A]) -> "DatasetFactory":
        return self.update(defaults=defaults)

    def update(
        self,
        effects: Optional[EffectSet[A]] = None,
        cache: Optional[Cache[A]] = None,
        dispatch: Optional[Union[Evaluatable[Hashable], str]] = None,
        defaults: Optional[Dict[str, MaybeEvaluatable[A]]] = None,
        abstract: Optional[bool] = None,
    ) -> "DatasetFactory":
        return DatasetFactory(
            effects=OrderedDict([*self.effects.items(), *(effects or {}).items()]),
            cache=cache or self.cache,
            dispatch=dispatch or self.dispatch,
            defaults={**self.defaults, **(defaults or {})},
            abstract=abstract if abstract is not None else self.abstract,
        )

    @property
    def nocache(self) -> "DatasetFactory":
        return self.update(cache=NoCache())


dataset: DatasetFactory = DatasetFactory()
abstractdataset: DatasetFactory = dataset(abstract=True)
