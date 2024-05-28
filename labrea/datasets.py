import concurrent.futures
import functools
import inspect
import logging
import math
import threading
import typing
import uuid
import warnings
from abc import ABC, abstractmethod
from collections import OrderedDict
from typing import (
    Any,
    Callable,
    Dict,
    Generic,
    List,
    Optional,
    Set,
    Type,
    TypeVar,
    Union,
)

from confectioner import mix

import labrea.multithreading

from ._aliases import default_alias, default_aliases
from ._import import require
from .cache import Cache, CacheInvalidationError, MemoryCache, NoCache
from .callbacks import Callbacks, EarlyExit, PostCallback, PreCallback
from .options import Option
from .pipelines import LabreaPipelineData
from .switch import Switch
from .types import Alias, Evaluatable, EvaluationError, JSONDict, MultiAlias, Value

A = TypeVar("A")
T = TypeVar("T")


class DatasetLike(ABC, Evaluatable[A]):
    name: str
    _callbacks: Callbacks[A]
    _cache: Cache[A]
    _options: JSONDict
    _lock: threading.Lock
    _logger: logging.Logger

    def __init__(
        self,
        cache: Union[Callable[[Evaluatable], Cache], Cache, None] = None,
        options: Optional[JSONDict] = None,
        callbacks: Union[Callbacks[A], Dict[str, PostCallback[A]], None] = None,
        lock: Optional[threading.Lock] = None,
        logger: Optional[logging.Logger] = None,
        name: Optional[str] = None,
        doc: Optional[str] = None,
        **kwargs,
    ):
        if isinstance(cache, Cache):
            self._cache = cache
        else:
            self._cache = (cache or MemoryCache)(self)
        self._options = options or {}

        if isinstance(callbacks, dict):
            self._callbacks = Callbacks(post=OrderedDict(callbacks))
        elif callbacks is None:
            self._callbacks = Callbacks()
        elif not isinstance(callbacks, Callbacks):
            raise TypeError(
                f"Callbacks must be a list of PostCallbacks, a Callbacks "
                f"object, or None, but is of type {type(callbacks)}."
            )
        else:
            self._callbacks = callbacks

        self.name = name or getattr(self, "__name__", str(self))  # type: ignore
        if doc is not None:
            self.__doc__ = doc

        self._lock = lock or threading.Lock()
        self._logger = logger or logging.getLogger(
            getattr(self, "__module__", __name__)
        )

    @property
    def callbacks(self) -> Callbacks[A]:
        return Callbacks(
            pre=OrderedDict(
                {
                    "__insert_options": self._insert_options,
                    "__cache_get": self._cache_get,
                    **self._callbacks.pre,
                    "__log_evaluation": self._log_evaluation,
                }
            ),
            post=OrderedDict({**self._callbacks.post, "__cache_set": self._cache_set}),
        )

    def add_pre_callbacks(
        self, *args: PreCallback[A], **kwargs: PreCallback[A]
    ) -> None:
        self._callbacks.pre.update(
            {
                **{
                    f"callback_{str(uuid.uuid4()).replace('-', '')}": callback
                    for callback in args
                },
                **kwargs,
            }
        )

    def add_post_callbacks(
        self, *args: PostCallback[A], **kwargs: PostCallback[A]
    ) -> None:
        self._callbacks.post.update(
            {
                **{
                    f"callback_{str(uuid.uuid4()).replace('-', '')}": callback
                    for callback in args
                },
                **kwargs,
            }
        )

    def add_callbacks(self, *args: PostCallback[A], **kwargs: PostCallback[A]) -> None:
        self.add_post_callbacks(*args, **kwargs)

    def _insert_options(self, obj: Evaluatable[A], options: JSONDict) -> JSONDict:
        return mix(options, self._options)  # type: ignore

    def _cache_get(self, obj: Evaluatable[A], options: JSONDict) -> None:
        if (
            options.get("LABREA", {})  # type: ignore
            .get("CACHE", {})
            .get("DISABLE", False)
        ):
            return

        keys = self._cache.keys(options)
        if self._cache.exists(keys):
            self._logger.debug(f"Labrea: Retrieving {self.name} " f"from cache")
            raise EarlyExit(self._cache.get(keys))

    def _log_evaluation(self, obj: Evaluatable[A], options: JSONDict):
        self._logger.info(f"Labrea: Evaluating {self.name}")

    def _cache_set(self, value: A, options: JSONDict) -> A:
        keys = self._cache.keys(options)
        self._cache.set(keys, value)
        if self._cache.exists(keys):
            return self._cache.get(keys)
        else:
            return value

    @staticmethod
    def _check_return(
        old: T, new: Union[T, LabreaPipelineData[Optional[T]], None]
    ) -> T:
        if isinstance(new, LabreaPipelineData):
            new = new.value

        return old if new is None else new

    @abstractmethod
    def _evaluate(self, options: JSONDict) -> A:
        pass

    def _evaluate_with_callbacks(self, options: JSONDict) -> A:
        for name, pre_callback in self.callbacks.pre.items():
            self._logger.debug(f"Labrea: Running pre-callback {name} for {self.name}")
            try:
                options = self._check_return(options, pre_callback(self, options))
            except EarlyExit as e:
                return e.value

        value = self._evaluate(options)

        for name, post_callback in self.callbacks.post.items():
            self._logger.debug(f"Labrea: Running post-callback {name} for {self.name}")
            try:
                value = self._check_return(value, post_callback(value, options))
            except EarlyExit as e:
                return e.value

        return value

    def evaluate(self, options: JSONDict) -> A:
        with self._lock:
            retries = 0
            max_retries: Union[int, float] = Option(
                "LABREA.CACHE.MAX_RETRIES", 5
            ).evaluate(options)
            max_retries = max_retries or math.inf
            while True:
                try:
                    return self._evaluate_with_callbacks(options)
                except CacheInvalidationError as e:
                    if retries < max_retries:
                        retries += 1
                        self._logger.debug(
                            f"Labrea: Caught CacheInvalidationError for "
                            f"{self.name}: {e.args}"
                        )
                        self._logger.debug(
                            f"Labrea: Performing retry {retries} of "
                            f"{max_retries} for {self.name}"
                        )
                        continue
                    else:
                        raise EvaluationError(
                            f"Cache invalid for {self.name} - "
                            f"maximum retries exceeded."
                        ) from e


class Overload(DatasetLike[A]):
    """Overload Class, an Evaluatable wrapper for a function.

    An Overload is an individual implementation of a Dataset.

    Notes
    -----
    This class is not intended to be instantiated directly. Instead, use
    <mydataset>.overload as a decorator.

    See Also
    --------
    :class:`Dataset`
    :meth:`Dataset.overload`
    """

    _definition: Callable[..., A]
    _parent: Optional["Dataset"]
    _eval_kwargs: Dict[str, Evaluatable]
    _init_kwargs: Dict[str, Any]
    _aliases: MultiAlias

    def __init__(
        self,
        definition: Callable[..., A],
        parent: Optional["Dataset"] = None,
        defaults: Optional[Dict[str, Evaluatable]] = None,
        aliases: Optional[MultiAlias] = None,
        cache: Union[Callable[[Evaluatable], Cache], Cache, None] = NoCache,
        _stack: int = 0,
        **kwargs,
    ):
        definition_closure = inspect.getclosurevars(definition)
        enclosed = {**definition_closure.globals, **definition_closure.nonlocals}
        for key, val in enclosed.items():
            if isinstance(val, Evaluatable):
                warnings.warn(
                    f"Variable {key} in the body of {definition.__name__} "
                    f"refers to a {type(val)} object from the enclosing "
                    f"scope. Did you mean to include {key} in the function "
                    f"signature like "
                    f'"def {definition.__name__}({key}={key}, ...)"?',
                    stacklevel=_stack + 1,
                )

        signature = inspect.signature(definition)
        defaults = {} if defaults is None else defaults
        eval_kwargs = {
            **{key: val.default for key, val in signature.parameters.items()},
            **defaults,
        }

        self._init_kwargs = {
            "definition": definition,
            "defaults": defaults,
            "parent": parent,
            "aliases": aliases,
            **kwargs,
        }

        for key, val in eval_kwargs.items():
            if val is signature.empty:
                raise TypeError(
                    f"Dataset arguments must all have defaults, but {key} has "
                    f"no default provided in {definition}."
                )
            if not isinstance(val, Evaluatable):
                eval_kwargs[key] = Value(val)

        functools.update_wrapper(self, definition)

        self._definition = definition  # type: ignore
        self._parent = parent
        self._eval_kwargs = eval_kwargs
        self._aliases = aliases or default_aliases(self)

        if self._parent is not None:
            for alias in self._aliases:
                self._parent.register(alias, self)

        super().__init__(
            definition=definition,
            parent=parent,
            defaults=defaults,
            aliases=aliases,
            cache=cache,
            **kwargs,
        )

    def validate(self, options: JSONDict) -> None:
        """Validate the Overload.

        Validate the Overload using the options dictionary, recursively
        validating all dependencies.

        See Also
        --------
        :meth:`labrea.types.Validatable.validate`
        """
        for dependency in self._eval_kwargs.values():
            dependency.validate(options)

    def keys(self, options: JSONDict) -> Set[str]:
        """Get the keys that this Overload depends on.

        Get the keys that this Overload depends on using the options
        dictionary, recursively getting keys for all dependencies.

        See Also
        --------
        :meth:`labrea.types.Validatable.keys`
        """
        return {
            key
            for dependency in self._eval_kwargs.values()
            for key in dependency.keys(options)
        }

    def _evaluate_inputs(self, options: JSONDict) -> Dict[str, Any]:
        if labrea.multithreading.is_parallel():
            return self._evaluate_inputs_multithread(options)
        else:
            return self._evaluate_inputs_singlethread(options)

    def _evaluate_inputs_multithread(self, options: JSONDict) -> Dict[str, Any]:
        result = {}

        with concurrent.futures.ThreadPoolExecutor() as executor:
            future_to_key = {
                executor.submit(
                    lambda evaluatable, opts: evaluatable.evaluate(opts), val, options
                ): key
                for key, val in self._eval_kwargs.items()
            }

            for future in concurrent.futures.as_completed(future_to_key):
                key = future_to_key[future]
                result[key] = future.result()

        return result

    def _evaluate_inputs_singlethread(self, options: JSONDict) -> Dict[str, Any]:
        return {key: val.evaluate(options) for key, val in self._eval_kwargs.items()}

    def _evaluate(self, options: JSONDict) -> A:
        return self._definition(**self._evaluate_inputs(options))

    def cached(self, options: JSONDict) -> bool:
        return options in self._cache

    def where(self, **kwargs) -> "Overload[A]":
        return OverloadFactory(
            dataset=self._parent,
            defaults={**self._init_kwargs.get("defaults", {}), **kwargs},
            cache=self._init_kwargs.get("cache", None),
            callbacks=self._callbacks,
        ).wrap(self._definition)

    def cache(self, cache: Callable[[Evaluatable], Cache]) -> "Overload[A]":
        return OverloadFactory(
            dataset=self._parent,
            defaults=self._init_kwargs.get("defaults", {}).copy(),
            cache=cache,
            callbacks=self._callbacks,
        ).wrap(self._definition)

    @property
    def nocache(self) -> "Overload[A]":
        return self.cache(NoCache)

    def __repr__(self):
        words = []

        if self._parent is None:
            words.append("Unbound")

        words.append("Overload")

        if self.__qualname__:
            words.append(self.__qualname__)

        if self._parent is not None:
            words.extend(["of", self._parent.__repr__()])

        return f'<{" ".join(words)}>'


class Dataset(DatasetLike[A]):
    """Dataset Class, an Evaluatable wrapper for a function.

    A Dataset is an Evaluatable wrapper around a function whose arguments are
    Evaluatables. The Dataset will evaluate the defaults to each argument
    using the options dictionary, and then pass the evaluated values to the
    function. The Dataset will then cache the result of the function call
    for the specific options used to evaluate that call.

    A Dataset has 0 or more Overloads, which are the different implementations
    of the Dataset. A Dataset can be abstract, in which case it has no
    Overloads, or it can be concrete, in which case it has at least one
    Overload. The default Overload is the one that will be used if no
    implementation is specified. Which Overload is used can be specified
    using the LABREA.IMPLEMENTATIONS.<dataset> option in the options,
    or by providing a dispatch Evaluatable to the Dataset.

    Notes
    -----
    This class is not intended to be instantiated directly. Instead, use the
    :func:`dataset` or :func:`abstractdataset` factory functions,
    which normally should be used as decorators.
    """

    _overloads: Switch[A]
    _alias: Alias

    def __init__(self, overloads: Switch[A], alias: Alias = None, **kwargs):
        self._overloads = overloads
        self._alias = alias or default_alias(self)

        super().__init__(overloads=overloads, alias=alias, **kwargs)

    @property
    def overload(self) -> "OverloadFactory":
        """Decorator for creating an Overload for this Dataset.

        This method is used to create an Overload for this Dataset. It can be
        used as a decorator, like :code:`@<dataset>.overload`, or as a
        function, like :code:`<dataset>.overload(<definition>)`.

        Parameters
        ----------
        definition : Callable[..., A]
            The function to wrap in an Overload.
        where : Dict[str, Any], optional
            Default values for arguments to the Overload.
        cache : Callable[[Overload], Cache], optional
            A callable that returns a Cache object for the Overload. If not
            provided, a MemoryCache will be used.
        alias : Alias, optional
            An Alias for the Overload. If not provided, the name of
            the Overload will be used.
        aliases : MultiAlias, optional
            A list of Aliases for the Overload. If not provided, the name of
            the Overload will be used.

        See Also
        --------
        :class:`Overload`
        """
        return OverloadFactory(dataset=self)

    def register(self, alias: Alias, overload: Overload[A]):
        """Register an Overload for this Dataset.

        This method is used to register an Overload for this Dataset. It is
        not normally used directly, but is used by the OverloadFactory.
        """
        self._overloads.lookup[alias] = overload

    def _import(self, options: JSONDict) -> None:
        require(*options.get("LABREA", {}).get("REQUIRE", []))  # type: ignore

        try:
            name = self._overloads.option.evaluate(options)
            if name not in self._overloads.lookup:
                warnings.warn(
                    f"Implementation {name} was specified for {self}, but "
                    f"could not be found. Falling back on default "
                    f"implementation if available."
                )
        except EvaluationError:
            pass

    def _evaluate(self, options: JSONDict) -> A:
        """Evaluate the Dataset.

        Identify the overload to use, and evaluate it using the options,
        recursively evaluating all dependencies.

        See Also
        --------
        :meth:`labrea.types.Evaluatable.evaluate`
        """
        self._import(options)
        return self._overloads.evaluate(options)

    def validate(self, options: JSONDict) -> None:
        """Validate the Dataset.

        Identify the overload to use, and validate it using the options,
        recursively validating all dependencies.

        See Also
        --------
        :meth:`labrea.types.Validatable.validate`
        """
        self._import(options)
        self._overloads.validate(options)

    def keys(self, options: JSONDict) -> Set[str]:
        """Get the keys that this Dataset depends on.

        Identify the overload to use, and get the keys that it depends on
        using the options, recursively getting all dependencies.

        See Also
        --------
        :meth:`labrea.types.Validatable.keys`
        """
        self._import(options)
        return self._overloads.keys(options)

    @property
    def is_abstract(self) -> bool:
        return not self._overloads.has_default

    @property
    def default(self) -> Overload[A]:
        return self._overloads.default  # type: ignore

    def where(self, **kwargs) -> Overload[A]:
        if self.is_abstract:
            raise TypeError("Cannot use where method on an abstract dataset.")

        return self.default.where(**kwargs)

    def cache(self, cache: Callable[[Evaluatable], Cache]) -> Overload[A]:
        if self.is_abstract:
            raise TypeError("Cannot use cache method on an abstract dataset.")

        return self.default.cache(cache)

    @property
    def nocache(self) -> "Dataset[A]":
        return self.with_cache(NoCache)

    def with_options(self, options: JSONDict) -> "Dataset[A]":
        return Dataset(
            self._overloads,
            alias=self._alias,
            options=mix(self._options, options),  # type: ignore
            callbacks=self._callbacks,
            cache=self._cache,
            name=self.name,
            doc=self.__doc__,
        )

    def with_cache(
        self, cache: Union[Callable[[Evaluatable], Cache], Cache]
    ) -> "Dataset[A]":
        return Dataset(
            self._overloads,
            alias=self._alias,
            options=self._options,
            callbacks=self._callbacks,
            cache=cache,
            name=self.name,
            doc=self.__doc__,
        )

    def set_cache(self, cache: Union[Callable[[Evaluatable], Cache], Cache]):
        self._cache = cache if isinstance(cache, Cache) else cache(self)

    def __repr__(self):
        return f'<Dataset {self._alias or "object"}>'


class OverloadFactory(Generic[A]):
    _dataset: Optional[Dataset[A]]
    _defaults: Dict[str, Any]
    _cache: Union[Type[Cache], Callable[[Evaluatable], Cache]]
    _aliases: MultiAlias
    _callbacks: Optional[Callbacks[A]]
    _options: JSONDict

    def __init__(
        self,
        dataset: Optional[Dataset[A]] = None,
        defaults: Optional[Dict[str, Any]] = None,
        cache: Optional[Callable[[Evaluatable], Cache]] = None,
        aliases: Optional[MultiAlias] = None,
        callbacks: Optional[Callbacks[A]] = None,
        options: Optional[JSONDict] = None,
    ):
        self._dataset = dataset
        self._defaults = defaults if defaults is not None else {}
        self._cache = cache if cache is not None else MemoryCache  # type: ignore
        self._aliases = aliases or []
        self._callbacks = callbacks
        self._options = options or {}

    @typing.overload
    def __call__(
        self,
        definition: Callable[..., A],
        /,
    ) -> Overload[A]:
        ...  # pragma: nocover

    @typing.overload
    def __call__(self, /, **kwargs: Any) -> "OverloadFactory":
        ...  # pragma: nocover

    def __call__(
        self,
        definition: Optional[Callable[..., A]] = None,
        /,
        *,
        where: Optional[Dict[str, Any]] = None,
        cache: Optional[Callable[[Evaluatable], Cache]] = None,
        alias: Optional[Alias] = None,
        aliases: Optional[MultiAlias] = None,
        callbacks: Union[
            Callbacks[A], List[PostCallback[A]], Dict[str, PostCallback[A]], None
        ] = None,
        options: Optional[JSONDict] = None,
        _stack: int = 1,
        **kwargs,
    ) -> Union["OverloadFactory[A]", Overload[A]]:
        aliases = aliases or []
        if alias is not None:
            aliases.append(alias)

        factory = self
        if where is not None:
            factory = factory.where(**where)
        if cache is not None:
            factory = factory.cache(cache)
        if aliases:
            factory = factory.alias(aliases)
        if callbacks:
            factory = factory.callbacks(callbacks)
        if options:
            factory = factory.options(options)

        if definition is None:
            return factory

        return factory.wrap(definition, _stack=_stack + 1)

    def wrap(self, definition: Callable[..., A], _stack: int = 1) -> Overload[A]:
        overload = Overload(
            definition=definition,
            parent=self._dataset,
            cache=self._cache,
            defaults=self._defaults,
            aliases=self._aliases,
            callbacks=self._callbacks,
            options=self._options,
            doc=getattr(definition, "__doc__", None),
            _stack=_stack + 1,
        )

        return overload

    def where(self, **kwargs) -> "OverloadFactory[A]":
        return OverloadFactory(
            self._dataset,
            defaults={**self._defaults, **kwargs},
            cache=self._cache,
            aliases=self._aliases,
            callbacks=self._callbacks,
            options=self._options,
        )

    def cache(self, cache: Callable[[Evaluatable], Cache]) -> "OverloadFactory[A]":
        return OverloadFactory(
            self._dataset,
            defaults=self._defaults,
            cache=cache,
            aliases=self._aliases,
            callbacks=self._callbacks,
            options=self._options,
        )

    @property
    def nocache(self) -> "OverloadFactory[A]":
        return self.cache(NoCache)

    def alias(self, aliases: MultiAlias) -> "OverloadFactory[A]":
        return OverloadFactory(
            self._dataset,
            defaults=self._defaults,
            cache=self._cache,
            aliases=aliases,
            callbacks=self._callbacks,
            options=self._options,
        )

    def callbacks(
        self,
        callbacks: Union[
            Callbacks[A], List[PostCallback[A]], Dict[str, PostCallback[A]]
        ],
    ) -> "OverloadFactory[A]":
        if isinstance(callbacks, dict):
            callbacks = Callbacks(post=OrderedDict(callbacks))
        elif isinstance(callbacks, list):
            callbacks = Callbacks(
                post=OrderedDict(
                    {
                        f'callback_{str(uuid.uuid4()).replace("-", "")}': callback
                        for callback in callbacks
                    }
                )
            )
        return OverloadFactory(
            self._dataset,
            defaults=self._defaults,
            cache=self._cache,
            aliases=self._aliases,
            callbacks=callbacks,
            options=self._options,
        )

    def options(self, options: JSONDict) -> "OverloadFactory[A]":
        return OverloadFactory(
            self._dataset,
            defaults=self._defaults,
            cache=self._cache,
            aliases=self._aliases,
            callbacks=self._callbacks,
            options=mix(self._options, options),  # type: ignore
        )


class DatasetFactory(Generic[A]):
    """A factory function for creating Datasets.

    Used to create Datasets. Normally used as a decorator, like @dataset.
    Can either be used bare like @dataset, or with extra arguments like
    @dataset(dispatch=...).

    Parameters
    ----------
    definition : Callable[..., A]
        The function to wrap in a Dataset.
    dispatch : Evaluatable[str], optional
        An Evaluatable that returns the name of the implementation to use.
        If not provided, the LABREA.IMPLEMENTATIONS.<dataset> option will
        be used.
    abstract : bool, optional
        Whether the Dataset is abstract or not. If abstract, it will have
        no default implementation.
    defaults : Dict[str, Any], optional
        Default values for arguments to the Dataset.
    cache : Callable[[Overload], Cache], optional
        A callable that returns a Cache object for the Dataset. If not
        provided, a MemoryCache will be used.
    callbacks : Callbacks[A] | List[PostCallback[A]] | Dict[str, PostCallback[A]], optional
        Callbacks to be used for the Dataset. If a list is provided, the names
        will be generated automatically.
    alias : Alias, optional
        An Alias for the default Overload. If not provided, the name of
        the Dataset will be used.


    Example Usage
    -------------
    >>> from labrea import dataset, Option
    >>> @dataset
    ... def my_dataset(a: str = Option('A')) -> str:
    ...     return a
    >>>
    >>> print(my_dataset({'A': 'Hello World!'})) # Hello World!
    >>>
    >>> @dataset(dispatch=Option('OVERLOADED_DATASET.DISPATCH'))
    ... def overloaded_dataset(b: str = Option('A')) -> str:
    ...     return b
    >>>
    >>> @overloaded_dataset.overload(alias='OVERLOAD_1')
    ... def _overload_1(b: str = Option('')) -> str:
    ...     return b.upper()
    >>>
    >>> print(overloaded_dataset({
    ...     'OVERLOADED_DATASET.DISPATCH': 'OVERLOAD_1',
    ...     'A': 'Hello World!'}
    ... )) # HELLO WORLD!


    See Also
    --------
    :class:`Dataset`
    """

    _dispatch: Optional[Evaluatable[str]]
    _abstract: bool
    _defaults: Dict[str, Any]
    _cache: Union[Type[Cache], Callable[[Evaluatable], Cache], None]
    _alias: Optional[Alias]
    _callbacks: Optional[Callbacks[A]]
    _options: JSONDict

    def __init__(
        self,
        dispatch: Optional[Evaluatable[str]] = None,
        abstract: bool = False,
        defaults: Optional[Dict[str, Any]] = None,
        cache: Optional[Callable[[Evaluatable], Cache]] = None,
        alias: Optional[Alias] = None,
        callbacks: Optional[Callbacks[A]] = None,
        options: Optional[JSONDict] = None,
    ):
        self._dispatch = dispatch
        self._abstract = abstract
        self._defaults = defaults or {}
        self._cache = cache
        self._alias = alias
        self._callbacks = callbacks
        self._options = options or {}

    @typing.overload
    def __call__(
        self,
        definition: Callable[..., A],
        /,
    ) -> Dataset[A]:
        ...  # pragma: nocover

    @typing.overload
    def __call__(self, /, **kwargs: Any) -> "DatasetFactory[A]":
        ...  # pragma: nocover

    def __call__(
        self,
        definition: Optional[Callable[..., A]] = None,
        /,
        *,
        dispatch: Optional[Evaluatable[str]] = None,
        where: Optional[Dict[str, Any]] = None,
        cache: Optional[Callable[[Evaluatable], Cache]] = None,
        alias: Optional[Alias] = None,
        callbacks: Union[
            Callbacks[A], List[PostCallback[A]], Dict[str, PostCallback[A]], None
        ] = None,
        options: Optional[JSONDict] = None,
        _stack: int = 1,
        **kwargs,
    ) -> Union["DatasetFactory[A]", Dataset[A]]:
        factory = self
        if dispatch is not None:
            factory = factory.dispatch(dispatch)
        if where is not None:
            factory = factory.where(**where)
        if cache is not None:
            factory = factory.cache(cache)
        if alias is not None:
            factory = factory.alias(alias)
        if callbacks is not None:
            factory = factory.callbacks(callbacks)
        if options is not None:
            factory = factory.options(options)

        if definition is None:
            return factory

        return factory.wrap(definition, _stack=_stack + 1)

    def __getattribute__(self, item):
        if super().__getattribute__("_abstract") and item in ("cache", "where"):
            warnings.warn(
                f"Method {item} has no effect for an abstract dataset", stacklevel=1
            )

        return super().__getattribute__(item)

    def wrap(self, definition: Callable[..., A], _stack: int = 1) -> Dataset[A]:
        alias = self._alias or default_alias(definition)

        dispatch = self._dispatch or Option(f"LABREA.IMPLEMENTATIONS.{alias}")
        overloads: Switch[A] = Switch(dispatch, {})

        dataset = Dataset(
            overloads,
            alias=alias,
            doc=getattr(definition, "__doc__", None),
            cache=self._cache,
            name=getattr(definition, "__name__", None),
            callbacks=self._callbacks,
            options=self._options,
        )

        if not self._abstract:
            overloads.default = Overload(
                definition, parent=dataset, defaults=self._defaults
            )

        return dataset

    def dispatch(self, dispatch: Union[str, Evaluatable[str]]) -> "DatasetFactory[A]":
        dispatch_: Evaluatable[str]
        if isinstance(dispatch, str):
            dispatch_ = Option(dispatch)
        else:
            dispatch_ = dispatch

        return DatasetFactory(
            dispatch=dispatch_,
            abstract=self._abstract,
            defaults=self._defaults,
            cache=self._cache,
            alias=self._alias,
            callbacks=self._callbacks,
            options=self._options,
        )

    def cache(self, cache: Callable[[Evaluatable], Cache]) -> "DatasetFactory[A]":
        return DatasetFactory(
            dispatch=self._dispatch,
            abstract=self._abstract,
            defaults=self._defaults,
            cache=cache,
            alias=self._alias,
            callbacks=self._callbacks,
            options=self._options,
        )

    def where(self, **kwargs) -> "DatasetFactory[A]":
        return DatasetFactory(
            dispatch=self._dispatch,
            abstract=self._abstract,
            defaults={**self._defaults, **kwargs},
            cache=self._cache,
            alias=self._alias,
            callbacks=self._callbacks,
            options=self._options,
        )

    @property
    def nocache(self) -> "DatasetFactory[A]":
        return self.cache(NoCache)

    def alias(self, alias: Alias) -> "DatasetFactory[A]":
        return DatasetFactory(
            dispatch=self._dispatch,
            abstract=self._abstract,
            defaults=self._defaults,
            cache=self._cache,
            alias=alias,
            callbacks=self._callbacks,
            options=self._options,
        )

    def callbacks(
        self,
        callbacks: Union[
            Callbacks[A],
            List[PostCallback[A]],
            Dict[str, PostCallback[A]],
        ],
    ) -> "DatasetFactory[A]":
        if isinstance(callbacks, dict):
            callbacks = Callbacks(post=OrderedDict(callbacks))
        elif isinstance(callbacks, list):
            callbacks = Callbacks(
                post=OrderedDict(
                    {
                        f'callback_{str(uuid.uuid4()).replace("-", "")}': callback
                        for callback in callbacks
                    }
                )
            )
        return DatasetFactory(
            dispatch=self._dispatch,
            abstract=self._abstract,
            defaults=self._defaults,
            cache=self._cache,
            alias=self._alias,
            callbacks=callbacks,
            options=self._options,
        )

    def options(self, options: JSONDict) -> "DatasetFactory[A]":
        return DatasetFactory(
            dispatch=self._dispatch,
            abstract=self._abstract,
            defaults=self._defaults,
            cache=self._cache,
            alias=self._alias,
            callbacks=self._callbacks,
            options=mix(self._options, options),  # type: ignore
        )


dataset: DatasetFactory = DatasetFactory()
abstractdataset: DatasetFactory = DatasetFactory(abstract=True)
abstractdataset.__doc__ = """Factory function for creating abstract Datasets.

    This is just an alias for :code:`dataset(abstract=True)`.

    See Also
    --------
    :func:`labrea.datasets.dataset`
    :class:`Dataset`
"""
