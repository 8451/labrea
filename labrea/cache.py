from abc import ABC, abstractmethod
from typing import Any, Callable, Dict, Generic, Optional, Set, TypeVar, Union, overload

from . import runtime
from .option import Option
from .types import Evaluatable, Options

A = TypeVar("A")


class CacheFailure(Exception):
    """An exception raised when a cache operation fails."""

    evaluatable: Evaluatable
    options: Options
    cache: "Cache"


class CacheGetFailure(CacheFailure):
    """An exception raised when a cache get operation fails."""

    def __init__(
        self, evaluatable: Evaluatable, options: Options, cache: "Cache"
    ) -> None:
        self.evaluatable = evaluatable
        self.options = options
        self.cache = cache

        super().__init__(f"Failed to retrieve {evaluatable} from cache {cache}")


class CacheSetFailure(CacheFailure):
    """An exception raised when a cache set operation fails."""

    evaluatable: Evaluatable
    options: Options
    cache: "Cache"
    value: Any

    def __init__(
        self, evaluatable: Evaluatable, options: Options, cache: "Cache", value: Any
    ) -> None:
        self.evaluatable = evaluatable
        self.options = options
        self.cache = cache
        self.value = value

        super().__init__(f"Failed to add value {value} from {evaluatable} to {cache}")


class CacheExistsFailure(CacheFailure):
    """An exception raised when a cache exists operation fails."""

    evaluatable: Evaluatable
    options: Options
    cache: "Cache"

    def __init__(
        self, evaluatable: Evaluatable, options: Options, cache: "Cache"
    ) -> None:
        self.evaluatable = evaluatable
        self.options = options
        self.cache = cache

        super().__init__(f"Failed to check if {evaluatable} exists in cache {cache}")


class Cache(Generic[A], ABC):
    """A class representing a cache of values that can be evaluated."""

    @abstractmethod
    def get(self, evaluatable: Evaluatable[A], options: Options) -> A:
        """Get a key from the cache.

        Arguments
        ---------
        evaluatable: Evaluatable
            The evaluatable to get from the cache.
        options : Options
            The options dictionary to evaluate against.

        Returns
        -------
        A
            The value from the cache.

        Raises
        ------
        CacheGetFailure
            If the key cannot be retrieved from the cache.
        """
        raise NotImplementedError  # pragma: nocover

    @abstractmethod
    def set(self, evaluatable: Evaluatable[A], options: Options, value: A) -> None:
        """Set a key in the cache.

        Arguments
        ---------
        evaluatable: Evaluatable
            The evaluatable to set in the cache.
        options : Options
            The options dictionary to evaluate against.
        value : A
            The value to set in the cache.

        Raises
        ------
        CacheSetFailure
            If the key cannot be set in the cache.
        """
        raise NotImplementedError  # pragma: nocover

    def exists(self, evaluatable: Evaluatable[A], options: Options) -> bool:
        """Check if a key exists in the cache.

        Arguments
        ---------
        evaluatable: Evaluatable
            The evaluatable to check in the cache.
        options : Options
            The options dictionary to evaluate against.

        Returns
        -------
        bool
            Whether the value exists in the cache.

        Raises
        ------
        CacheExistsFailure
            If the existence of the key cannot be checked in the cache.
        """
        try:
            self.get(evaluatable, options)
            return True
        except CacheGetFailure:
            return False


class NoCache(Cache[Any]):
    """A class representing a cache that does not store any values."""

    def get(self, evaluatable: Evaluatable, options: Options) -> Any:
        raise CacheGetFailure(evaluatable, options, self)

    def set(self, evaluatable: Evaluatable, options: Options, value: Any) -> None:
        pass


class MemoryCache(Cache[A]):
    """A class representing a cache that stores values in memory."""

    _cache: Dict[bytes, A]

    def __init__(self) -> None:
        self._cache = {}

    def get(self, evaluatable: Evaluatable, options: Options) -> A:
        try:
            return self._cache[evaluatable.fingerprint(options)]
        except KeyError as e:
            raise CacheGetFailure(evaluatable, options, self) from e

    def set(self, evaluatable: Evaluatable, options: Options, value: A) -> None:
        self._cache[evaluatable.fingerprint(options)] = value

    def exists(self, evaluatable: Evaluatable, options: Options) -> bool:
        return evaluatable.fingerprint(options) in self._cache


class CacheSetRequest(runtime.Request[A]):
    evaluatable: Evaluatable
    options: Options
    value: A
    cache: Cache[A]

    def __init__(
        self, evaluatable: Evaluatable[A], options: Options, value: A, cache: Cache[A]
    ):
        self.evaluatable = evaluatable
        self.options = options
        self.value = value
        self.cache = cache


class CacheGetRequest(runtime.Request[A]):
    evaluatable: Evaluatable[A]
    options: Options
    cache: Cache[A]

    def __init__(self, evaluatable: Evaluatable, options: Options, cache: Cache[A]):
        self.evaluatable = evaluatable
        self.options = options
        self.cache = cache


class CacheExistsRequest(runtime.Request[bool]):
    evaluatable: Evaluatable
    options: Options
    cache: Cache

    def __init__(self, evaluatable: Evaluatable, options: Options, cache: Cache):
        self.evaluatable = evaluatable
        self.options = options
        self.cache = cache


def _cache_disabled(
    request: Union[CacheSetRequest, CacheGetRequest, CacheExistsRequest]
) -> bool:
    return Option("LABREA.CACHE.DISABLED", Option("LABREA.CACHE.DISABLE", False))(
        request.options
    )


@CacheSetRequest.handle
def set_cache_handler(request: CacheSetRequest[A]) -> A:
    if _cache_disabled(request):
        return _disabled_set_cache_handler(request)

    request.cache.set(request.evaluatable, request.options, request.value)
    try:
        return request.cache.get(request.evaluatable, request.options)
    except CacheGetFailure:
        return request.value


@CacheGetRequest.handle
def get_cache_handler(request: CacheGetRequest[A]) -> A:
    if _cache_disabled(request):
        return _disabled_get_cache_handler(request)

    return request.cache.get(request.evaluatable, request.options)


@CacheExistsRequest.handle
def exists_cache_handler(request: CacheExistsRequest) -> bool:
    if _cache_disabled(request):
        return _disabled_exists_cache_handler(request)

    return request.cache.exists(request.evaluatable, request.options)


def _disabled_set_cache_handler(request: CacheSetRequest[A]) -> A:
    return request.value


def _disabled_get_cache_handler(request: CacheGetRequest[A]) -> A:
    raise CacheGetFailure(request.evaluatable, request.options, request.cache)


def _disabled_exists_cache_handler(request: CacheExistsRequest) -> bool:
    return False


def disabled() -> runtime.Runtime:
    return runtime.handle(
        {
            CacheSetRequest: _disabled_set_cache_handler,
            CacheGetRequest: _disabled_get_cache_handler,
            CacheExistsRequest: _disabled_exists_cache_handler,
        }
    )


class Cached(Evaluatable[A]):
    """A class representing an Evaluatable that may be cached."""

    evaluatable: Evaluatable[A]
    cache: Cache[A]

    def __init__(self, evaluatable: Evaluatable[A], cache: Cache[A]):
        self.evaluatable = evaluatable
        self.cache = cache

    def evaluate(self, options: Options) -> A:
        if CacheExistsRequest(self.evaluatable, options, self.cache).run():
            try:
                return CacheGetRequest(self.evaluatable, options, self.cache).run()
            except CacheGetFailure:
                pass

        value = self.evaluatable.evaluate(options)

        return CacheSetRequest(self.evaluatable, options, value, self.cache).run()

    def validate(self, options: Options) -> None:
        if not CacheExistsRequest(self.evaluatable, options, self.cache).run():
            self.evaluatable.validate(options)

    def keys(self, options: Options) -> Set[str]:
        return self.evaluatable.keys(options)

    def explain(self, options: Optional[Options] = None) -> Set[str]:
        return self.evaluatable.explain(options)

    def __repr__(self) -> str:
        return f"CachedEvaluation({self.evaluatable!r}, {self.cache!r})"


@overload
def cached(__x: Evaluatable[A], cache: Optional[Cache[A]] = None) -> Evaluatable[A]:
    ...  # pragma: nocover


@overload
def cached(__x: Cache[A]) -> Callable[[Evaluatable[A]], Evaluatable[A]]:
    ...  # pragma: nocover


def cached(
    __x: Union[Cache[A], Evaluatable[A]],
    cache: Optional[Cache[A]] = None,
) -> Union[Callable[[Evaluatable[A]], Evaluatable[A]], Evaluatable[A]]:
    if isinstance(__x, Cache):
        return lambda evaluatable: cached(evaluatable, __x)
    else:
        cache = cache or MemoryCache()
        return Cached(__x, cache)
