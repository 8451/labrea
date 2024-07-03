from abc import ABC, abstractmethod
from typing import Any, Callable, Dict, Generic, Optional, Set, TypeVar, Union, overload

from . import runtime
from .types import Evaluatable, Options

A = TypeVar("A")


class CacheFailure(Exception):
    """An exception raised when a cache operation fails."""

    fingerprint: bytes
    options: Options
    cache: "Cache"


class CacheGetFailure(CacheFailure):
    """An exception raised when a cache get operation fails."""

    def __init__(self, fingerprint: bytes, options: Options, cache: "Cache") -> None:
        self.fingerprint = fingerprint
        self.options = options
        self.cache = cache

        super().__init__(
            f"Failed to retrieve item with fingerprint {fingerprint.hex()} from cache {cache}"
        )


class CacheSetFailure(CacheFailure):
    """An exception raised when a cache set operation fails."""

    fingerprint: bytes
    options: Options
    cache: "Cache"
    value: Any

    def __init__(
        self, fingerprint: bytes, options: Options, cache: "Cache", value: Any
    ) -> None:
        self.fingerprint = fingerprint
        self.options = options
        self.cache = cache
        self.value = value

        super().__init__(
            f"Failed to add key {value} with fingerprint {fingerprint.hex()} in cache {cache}"
        )


class CacheExistsFailure(CacheFailure):
    """An exception raised when a cache exists operation fails."""

    fingerprint: bytes
    options: Options
    cache: "Cache"

    def __init__(self, fingerprint: bytes, options: Options, cache: "Cache") -> None:
        self.fingerprint = fingerprint
        self.options = options
        self.cache = cache

        super().__init__(
            f"Failed to check if item with fingerprint {fingerprint.hex()} exists in cache {cache}"
        )


class Cache(Generic[A], ABC):
    """A class representing a cache of values that can be evaluated."""

    @abstractmethod
    def get(self, fingerprint: bytes, options: Options) -> A:
        """Get a key from the cache.

        Arguments
        ---------
        fingerprint : bytes
            The fingerprint of the key to get.
        options : Options
            The options dictionary to evaluate against.

        Returns
        -------
        A
            The key from the cache.

        Raises
        ------
        CacheGetFailure
            If the key cannot be retrieved from the cache.
        """
        raise NotImplementedError  # pragma: nocover

    @abstractmethod
    def set(self, fingerprint: bytes, options: Options, value: A) -> None:
        """Set a key in the cache.

        Arguments
        ---------
        fingerprint : bytes
            The fingerprint of the key to set.
        options : Options
            The options dictionary to evaluate against.
        value : A
            The key to set in the cache.

        Raises
        ------
        CacheSetFailure
            If the key cannot be set in the cache.
        """
        raise NotImplementedError  # pragma: nocover

    def exists(self, fingerprint: bytes, options: Options) -> bool:
        """Check if a key exists in the cache.

        Arguments
        ---------
        fingerprint : bytes
            The fingerprint of the key to check.
        options : Options
            The options dictionary to evaluate against.

        Returns
        -------
        bool
            Whether the key exists in the cache.

        Raises
        ------
        CacheExistsFailure
            If the existence of the key cannot be checked in the cache.
        """
        try:
            self.get(fingerprint, options)
            return True
        except CacheGetFailure:
            return False


class NoCache(Cache[Any]):
    """A class representing a cache that does not store any values."""

    def get(self, fingerprint: bytes, options: Options) -> Any:
        raise CacheGetFailure(fingerprint, options, self)

    def set(self, fingerprint: bytes, options: Options, value: Any) -> None:
        pass


class MemoryCache(Cache[A]):
    """A class representing a cache that stores values in memory."""

    _cache: Dict[bytes, A]

    def __init__(self) -> None:
        self._cache = {}

    def get(self, fingerprint: bytes, options: Options) -> A:
        try:
            return self._cache[fingerprint]
        except KeyError as e:
            raise CacheGetFailure(fingerprint, options, self) from e

    def set(self, fingerprint: bytes, options: Options, value: A) -> None:
        self._cache[fingerprint] = value

    def exists(self, fingerprint: bytes, options: Options) -> bool:
        return fingerprint in self._cache


class CacheSetRequest(runtime.Request[A]):
    fingerprint: bytes
    options: Options
    value: A
    cache: Cache[A]

    def __init__(self, fingerprint: bytes, options: Options, value: A, cache: Cache[A]):
        self.fingerprint = fingerprint
        self.options = options
        self.value = value
        self.cache = cache


class CacheGetRequest(runtime.Request[A]):
    fingerprint: bytes
    options: Options
    cache: Cache[A]

    def __init__(self, fingerprint: bytes, options: Options, cache: Cache[A]):
        self.fingerprint = fingerprint
        self.options = options
        self.cache = cache


class CacheExistsRequest(runtime.Request[bool]):
    fingerprint: bytes
    options: Options
    cache: Cache

    def __init__(self, fingerprint: bytes, options: Options, cache: Cache):
        self.fingerprint = fingerprint
        self.options = options
        self.cache = cache


@CacheSetRequest.handle
def set_cache_handler(request: CacheSetRequest[A]) -> A:
    request.cache.set(request.fingerprint, request.options, request.value)
    try:
        return request.cache.get(request.fingerprint, request.options)
    except CacheGetFailure:
        return request.value


@CacheGetRequest.handle
def get_cache_handler(request: CacheGetRequest[A]) -> A:
    return request.cache.get(request.fingerprint, request.options)


@CacheExistsRequest.handle
def exists_cache_handler(request: CacheExistsRequest) -> bool:
    return request.cache.exists(request.fingerprint, request.options)


def _disabled_set_cache_handler(request: CacheSetRequest[A]) -> A:
    return request.value


def _disabled_get_cache_handler(request: CacheGetRequest[A]) -> A:
    raise CacheGetFailure(request.fingerprint, request.options, request.cache)


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
        fingerprint = self.evaluatable.fingerprint(options)

        if CacheExistsRequest(fingerprint, options, self.cache).run():
            try:
                return CacheGetRequest(fingerprint, options, self.cache).run()
            except CacheGetFailure:
                pass

        value = self.evaluatable.evaluate(options)

        return CacheSetRequest(fingerprint, options, value, self.cache).run()

    def validate(self, options: Options) -> None:
        fingerprint = self.evaluatable.fingerprint(options)

        if not CacheExistsRequest(fingerprint, options, self.cache).run():
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
