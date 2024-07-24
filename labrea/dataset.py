import sys

if sys.version_info < (3, 10):
    from typing_extensions import ParamSpec
else:
    from typing import ParamSpec

import functools
import logging
from typing import (
    Any,
    Callable,
    Dict,
    Generic,
    Hashable,
    List,
    Optional,
    Set,
    TypeVar,
    Union,
    overload,
)

from confectioner import mix

from ._missing import MISSING, MaybeMissing
from .application import FunctionApplication
from .cache import Cache, MemoryCache, NoCache, cached
from .computation import CallbackEffect, ChainedEffect, Computation, Effect
from .logging import Logged
from .option import Option, WithDefaultOptions, WithOptions
from .overload import Overloaded
from .types import Evaluatable, MaybeEvaluatable, Options, Value

A = TypeVar("A", covariant=True)
P = ParamSpec("P")
Callback = MaybeEvaluatable[Callable[[A], None]]


class Dataset(Evaluatable[A]):
    """A class representing a dataset.

    Datasets are the building blocks of Labrea programs. They represent the result of performing
    some calculation over a set of inputs. Datasets can be composed together to create complex
    call graphs that represent the flow of data through a program. Datasets are parameterized
    using :code:`Options`, which allow for user input.

    Datasets are not created directly; instead, they are created using the :code:`dataset`
    decorator. This decorator takes a function that defines the dataset and returns a new
    :code:`Dataset` object. When a dataset is evaluated, the default values to each argument
    are evaluated using the provided options. The dataset is then evaluated using the
    evaluated arguments.


    Example Usage
    -------------
    >>> @dataset
    ... def a_squared(a: float = Option('A')) -> float:
    ...     return a ** 2
    >>>
    >>> @dataset
    ... def b_squared(b: float = Option('B')) -> float:
    ...     return b ** 2
    >>>
    >>> @dataset
    ... def hypotenuse(a2: float = a_squared, b2: float = b_squared) -> float:
    ...     return (a2 + b2) ** 0.5
    >>>
    >>> hypotenuse({'A': 3, 'B': 4})
    5.0
    """

    overloads: Overloaded[A]
    effects: List[Effect[A]]
    cache: Cache[A]
    options: Options
    default_options: Options
    _effects_disabled: bool

    def __init__(
        self,
        overloads: Overloaded[A],
        effects: List[Effect[A]],
        cache: Cache[A],
        options: Options,
        default_options: Options,
    ):
        self.overloads = overloads
        self.effects = effects.copy()
        self.cache = cache
        self.options = options
        self.default_options = default_options
        self._effects_disabled = False

    @property
    def _composed(self) -> Evaluatable[A]:
        computation = Computation(
            self.overloads,
            ChainedEffect(*self.effects),
        )
        return WithDefaultOptions(
            WithOptions(
                cached(
                    Logged(
                        self.overloads if self._effects_disabled else computation,
                        level=logging.INFO,
                        name=self.__module__,
                        msg=f"Labrea: Evaluating {self!r}",
                    ),
                    self.cache,
                ),
                self.options,
            ),
            self.default_options,
        )

    def evaluate(self, options: Options) -> A:
        """Evaluates the dataset using the provided options."""
        return self._composed.evaluate(options)

    def validate(self, options: Options) -> None:
        """Validates the dataset using the provided options."""
        self._composed.validate(options)

    def keys(self, options: Options) -> Set[str]:
        """Returns the option keys required by the dataset."""
        return self._composed.keys(options)

    def explain(self, options: Optional[Options] = None) -> Set[str]:
        """Returns the option keys required by the dataset."""
        return self._composed.explain(options)

    def __repr__(self) -> str:
        kind = "AbstractDataset" if self.is_abstract else "Dataset"
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
        """Overloads the dataset with a new implementation. Used as a decorator.

        Overloading a dataset allows you to provide a new implementation for the dataset.
        Overloads are selected based on the dispatch value provided to the dataset. If no
        dispatch value is provided, the default implementation is used. Datasets can also
        be abstract, in which no default implementation is provided, and an error is raised
        if no overload can be found.

        Datasets must be created with a dispath argument in order to use overloads. If you
        are trying to overload a dataset that you do not own (i.e. from a third-party library),
        you can use my_dataset.set_dispatch(dispatch) to set the dispatch manually. The
        dispatch can be any Evaluatable object that returns a hashable value, or a string
        representing the Option key to use.

        Arguments
        ---------
        alias : Union[Hashable, List[Hashable]]
            The name or names to use for the overload.

        Returns
        -------
        FunctionApplication[P, A]
            The Evaluatable object representing the new implementation.


        Example Usage
        -------------
        >>> @dataset(dispatch='INPUT.SOURCE'))
        ... def input_data(path: str = Option('INPUT.PATH')) -> list[str]:
        ...     with open(path, 'r') as f:
        ...         return f.read()
        >>>
        >>> @input_data.overload('MOCK')
        ... def mock_input_data() -> list[str]:
        ...     return ['Mock', 'Data']
        >>>
        >>> input_data({'INPUT': {'PATH': 'data.txt'}})
        ['Data', 'From', 'File']
        >>> input_data({'INPUT': {'SOURCE': 'MOCK'}})
        ['Mock', 'Data']
        """
        if self.overloads.dispatch == Value(MISSING):
            raise ValueError(
                "Cannot add overloads to a dataset without a dispatch. Add a dispatch by using "
                "@dataset(dispatch=...) in the dataset definition. If you are trying to overload "
                "a dataset that you do not own (i.e. from a third-party library), you can use "
                "my_dataset.set_dispatch(dispatch) to set the dispatch manually."
            )

        if not isinstance(alias, list):
            alias = [alias]

        def decorator(func: Callable[P, A]) -> FunctionApplication[P, A]:
            overload_ = FunctionApplication.lift(func)
            for key in alias:
                self.register(key, overload_)
            return overload_

        return decorator

    def register(self, key: Hashable, value: Evaluatable[A]) -> None:
        """Registers a new overload for the dataset.

        Registers a new overload for the dataset. Can be used if you want an overload to be
        a pre-existing Evaluatable object, like an Option.

        Arguments
        ---------
        key : Hashable
            The name to use for the overload.
        value : Evaluatable[A]
            The Evaluatable object representing the new implementation.


        Example Usage
        -------------
        >>> @dataset(dispatch='INPUT.SOURCE'))
        ... def input_data(path: str = Option('INPUT.PATH')) -> list[str]:
        ...     with open(path, 'r') as f:
        ...         return f.read()
        >>>
        >>> input_data.register('MOCK', Value(['Mock', 'Data']))
        """
        self.overloads.register(key, value)

    def set_dispatch(self, dispatch: Evaluatable[Hashable]) -> None:
        """Sets the dispatch value for the dataset.

        This is a stateful operation that changes the dispatch value for the dataset. This
        is intended for use with third-party datasets that do not have a dispatch value set,
        but you want to add an overload to.

        Arguments
        ---------
        dispatch : Evaluatable[Hashable]
            The dispatch value to use for the dataset.
        """

        self.overloads = Overloaded(
            dispatch,
            self.overloads.lookup.copy(),
            default=self.overloads.default,
        )

    def set_cache(self, cache: Union[Cache[A], Callable[..., Cache[A]]]) -> None:
        """Sets the cache for the dataset.

        Sets the cache for the dataset. The cache can be any object that implements the Cache
        interface, or a callable that returns a Cache object. This is a stateful operation that
        changes the cache for the dataset. This is intended for use with third-party datasets
        that do not have a cache set, but you want to add a cache to.

        Arguments
        ---------
        cache : Union[Cache[A], Callable[..., Cache[A]]]
            The cache to use for the dataset.
        """
        cache = cache if isinstance(cache, Cache) else cache()
        if not isinstance(cache, Cache):
            raise TypeError(f"Invalid cache: {cache}")

        self.cache = cache

    def add_effects(self, *effects: Union[Effect[A], Callback[A]]) -> None:
        """Adds effects to the dataset.

        Adds effects to the dataset. Effects are applied to the dataset when it is evaluated.
        This is a stateful operation that changes the effects for the dataset. This is intended
        for use with third-party datasets that you would like to add effects to (i.e. logging).

        Arguments
        ---------
        effects : Union[Effect[A], Callback[A]]
            The effects to add to the dataset.
        """
        for effect in effects:
            if isinstance(effect, Effect):
                self.effects.append(effect)
            else:
                self.effects.append(CallbackEffect(effect))

    add_effect = add_effects

    def disable_effects(self) -> None:
        """Disables effects for the dataset.

        Disables effects for the dataset. Effects are not executed when the dataset is evaluated.
        This is a stateful operation that changes the effects for the dataset. This is intended
        for use with third-party datasets that you would like to disable effects for.
        """
        self._effects_disabled = True

    def enable_effects(self) -> None:
        """Enables effects for the dataset.

        Enables effects for the dataset. Effects are executed when the dataset is evaluated.
        This is a stateful operation that changes the effects for the dataset. This is intended
        for use with third-party datasets that you would like to enable effects for.
        """
        self._effects_disabled = False

    def with_options(self, options: Options) -> "Dataset[A]":
        """Returns a new dataset with the provided options pre-set.

        The provided options are pre-set, and cannot be overridden by the user. This
        can simplify the creation of multiple datasets that have the same inputs and
        calculations.

        Arguments
        ---------
        options : Options
            The options to pre-set for the dataset.

        Returns
        -------
        Dataset[A]
            A new dataset with the provided options pre-set.


        Example Usage
        -------------
        >>> @dataset
        ... def a_to_power(a: float = Option('A'), power: float = Option('POWER')) -> float:
        ...     return a ** power
        >>>
        >>> a_squared = a_to_power.with_options({'POWER': 2})
        """
        return Dataset(
            self.overloads,
            self.effects,
            self.cache,
            mix(self.options, options),  # type: ignore
            self.default_options,
        )

    def with_default_options(self, options: Options) -> "Dataset[A]":
        """Returns a new dataset with the provided options as default.

        The provided options are set as the default options for the dataset. These options
        can be overridden by the user. This can simplify the creation of multiple datasets
        that have the same inputs and calculations.

        Arguments
        ---------
        options : Options
            The options to set as the default for the dataset.

        Returns
        -------
        Dataset[A]
            A new dataset with the provided options as default.
        """
        return Dataset(
            self.overloads,
            self.effects,
            self.cache,
            self.options,
            mix(self.default_options, options),  # type: ignore
        )

    @property
    def default(self) -> MaybeMissing[Evaluatable[A]]:
        """The default implementation of the dataset."""
        return self.overloads.default

    @property
    def is_abstract(self) -> bool:
        """Whether the dataset is abstract (i.e. has no default implementation)."""
        return self.overloads.default is MISSING


class DatasetFactory(Generic[A]):
    effects: List[Effect[A]]
    cache: Union[Cache[A], Callable[..., Cache[A]], None]
    dispatch: Evaluatable[Hashable]
    defaults: Dict[str, Evaluatable[Any]]
    options: Options
    defaut_options: Options
    abstract: bool

    def __init__(
        self,
        effects: Optional[List[Effect[A]]] = None,
        cache: Union[Cache[A], Callable[..., Cache[A]], None] = None,
        dispatch: Union[Evaluatable[Hashable], str, None] = None,
        defaults: Optional[Dict[str, Any]] = None,
        abstract: bool = False,
        options: Optional[Options] = None,
        default_options: Optional[Options] = None,
    ):
        self.effects = effects or []
        self.cache = cache
        self.defaults = {
            key: Evaluatable.ensure(val) for key, val in (defaults or {}).items()
        }
        self.abstract = abstract
        self.options = options or {}
        self.default_options = default_options or {}

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
        effects: Optional[List[Union[Effect[A], Callback[A]]]] = ...,
        cache: Union[Cache[A], Callable[..., Cache[A]], None] = ...,
        dispatch: Optional[Union[Evaluatable[Hashable], str]] = ...,
        defaults: Optional[Dict[str, Any]] = ...,
        abstract: Optional[bool] = ...,
        options: Optional[Options] = ...,
        default_options: Optional[Options] = ...,
    ) -> Dataset[A]:
        ...  # pragma: no cover

    @overload
    def __call__(
        self,
        /,
        *,
        effects: Optional[List[Union[Effect[A], Callback[A]]]] = ...,
        cache: Union[Cache[A], Callable[..., Cache[A]], None] = ...,
        dispatch: Optional[Union[Evaluatable[Hashable], str]] = ...,
        defaults: Optional[Dict[str, Any]] = ...,
        abstract: Optional[bool] = ...,
        options: Optional[Options] = ...,
        default_options: Optional[Options] = ...,
    ) -> "DatasetFactory[A]":
        ...  # pragma: no cover

    @overload
    def __call__(
        self,
        definition: None,
        /,
        *,
        effects: Optional[List[Union[Effect[A,], Callback[A]]]] = ...,
        cache: Union[Cache[A], Callable[..., Cache[A]], None] = ...,
        dispatch: Optional[Union[Evaluatable[Hashable], str]] = ...,
        defaults: Optional[Dict[str, Any]] = ...,
        abstract: Optional[bool] = ...,
        options: Optional[Options] = ...,
        default_options: Optional[Options] = ...,
    ) -> "DatasetFactory[A]":
        ...  # pragma: no cover

    def __call__(
        self,
        definition: Optional[Callable[..., A]] = None,
        /,
        *,
        effects: Optional[List[Union[Effect[A], Callback[A]]]] = None,
        cache: Union[Cache[A], Callable[..., Cache[A]], None] = None,
        dispatch: Optional[Union[Evaluatable[Hashable], str]] = None,
        defaults: Optional[Dict[str, Any]] = None,
        abstract: Optional[bool] = None,
        options: Optional[Options] = None,
        default_options: Optional[Options] = None,
    ) -> Union["DatasetFactory", Dataset[A]]:
        _effects = [
            effect if isinstance(effect, Effect) else CallbackEffect(effect)
            for effect in (effects or [])
        ]
        factory = self.update(
            effects=_effects,
            cache=cache,
            dispatch=dispatch,
            defaults=defaults,
            abstract=abstract,
            options=options,
            default_options=default_options,
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

        cache: Cache
        if self.cache is None:
            cache = MemoryCache()
        elif callable(self.cache):
            cache = self.cache()
        elif isinstance(self.cache, Cache):
            cache = self.cache
        else:
            raise TypeError(f"Invalid cache: {self.cache}")

        _dataset = Dataset(
            overloads,
            effects=self.effects,
            cache=cache,
            options=self.options,
            default_options=self.default_options,
        )

        functools.update_wrapper(_dataset, definition, updated=())

        return _dataset

    def where(self, **defaults: Any) -> "DatasetFactory":
        return self.update(defaults=defaults)

    def update(
        self,
        effects: Optional[List[Effect[A]]] = None,
        cache: Union[Cache[A], Callable[..., Cache[A]], None] = None,
        dispatch: Optional[Union[Evaluatable[Hashable], str]] = None,
        defaults: Optional[Dict[str, Any]] = None,
        abstract: Optional[bool] = None,
        options: Optional[Options] = None,
        default_options: Optional[Options] = None,
    ) -> "DatasetFactory":
        return DatasetFactory(
            effects=[*self.effects, *(effects or [])],
            cache=cache or self.cache,
            dispatch=dispatch or self.dispatch,
            defaults={**self.defaults, **(defaults or {})},
            abstract=abstract if abstract is not None else self.abstract,
            options=options or self.options,
            default_options=default_options or self.default_options,
        )

    @property
    def nocache(self) -> "DatasetFactory":
        return self.update(cache=NoCache())


dataset: DatasetFactory = DatasetFactory()
abstractdataset: DatasetFactory = dataset(abstract=True)
