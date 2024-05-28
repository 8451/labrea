from abc import ABCMeta, abstractmethod
from typing import Generic, TypeVar

from confectioner.templating import get_dotted_key

from .types import Evaluatable, JSONDict, JSONType

A = TypeVar("A")


class CacheInvalidationError(Exception):
    """Raised when a cache is invalidated"""

    pass


def json_hash(json: JSONType):
    if isinstance(json, dict):
        keys = tuple(sorted(json.keys()))
        vals = [json[key] for key in keys]
        return hash((hash(keys), json_hash(vals)))
    if isinstance(json, list):
        return hash(tuple(json_hash(val) for val in json))
    else:
        return hash(json)


class Cache(Generic[A], metaclass=ABCMeta):
    """A cache for Datasets

    A cache is used to store the results of evaluating a Dataset. Every time a
    Dataset is evaluated, the cache is checked to see if the result has already
    been computed. If it has, the cached result is returned. If not, the
    Dataset is evaluated and the result is stored in the cache.

    Because the same Dataset can be evaluated with different options, the cache
    is keyed by the options dictionary. The keys returned by the Cache's
    keys() method are used to generate the key for the cache lookup, so the
    keys() method should return all keys that affect the evaluation of the
    Dataset.

    The Cache class is abstract and must be subclassed to implement the
    exists(), get(), and set() methods.
    """

    evaluatable: Evaluatable[A]

    def __init__(self, _evaluatable: Evaluatable[A]):
        """Create a new Cache

        Parameters
        ----------
        _evaluatable : Evaluatable[A]
            The Evaluatable that this Cache is caching.
        """
        self.evaluatable = _evaluatable

    @abstractmethod
    def exists(self, keys: JSONDict) -> bool:
        """Check if there is a cached value for the given keys

        Parameters
        ----------
        keys : JSONDict
            The keys to check for in the cache.

        Returns
        -------
        bool
            True if there is a cached value for the given keys,
            False otherwise.

        Raises
        ------
        CacheInvalidationError
            If the cached value is no longer valid.
        """
        ...  # pragma: nocover

    @abstractmethod
    def get(self, keys: JSONDict) -> A:
        """Get the cached value for the given keys

        Parameters
        ----------
        keys : JSONDict
            The keys to lookup in the cache

        Returns
        -------
        A
            The cached value for the given keys.

        Raises
        ------
        KeyError
            If there is no cached value for the given keys.
        CacheInvalidationError
            If the cached value is no longer valid.
        """
        ...  # pragma: nocover

    @abstractmethod
    def set(self, keys: JSONDict, value: A):
        """Set the cached value for the given keys

        Parameters
        ----------
        keys : JSONDict
            The keys to set in the cache
        value : A
            The value to set in the cache

        Raises
        ------
        CacheInvalidationError
            If the cached value is no longer valid.
        """
        ...  # pragma: nocover

    def keys(self, options: JSONDict) -> JSONDict:
        """Identify the keys that affect the evaluation of the Dataset

        Parameters
        ----------
        options : JSONDict
            The options dictionary to use to evaluate the Dataset

        Returns
        -------
        JSONDict
            The keys that affect the evaluation of the Dataset, and their
            values.
        """
        return {
            key: get_dotted_key(key, dict(options))
            for key in self.evaluatable.keys(options)
        }

    def __getitem__(self, options: JSONDict):
        keys = self.keys(options)
        return self.get(keys)

    def __setitem__(self, options: JSONDict, value: A):
        keys = self.keys(options)
        self.set(keys, value)

    def __contains__(self, options: JSONDict):
        keys = self.keys(options)
        return self.exists(keys)


class NoCache(Cache[A]):
    """A Cache that does not cache anything"""

    def exists(self, keys: JSONDict) -> bool:
        return False

    def get(self, keys: JSONDict) -> A:
        raise KeyError

    def set(self, keys: JSONDict, value: A):
        pass


class MemoryCache(Cache[A]):
    """A Cache that stores values in memory

    A simple in-memory cache that stores values in a dictionary.
    """

    _cache: dict

    def __init__(self, *args, **kwargs):
        self._cache = {}
        super().__init__(*args, **kwargs)

    def exists(self, keys: JSONDict) -> bool:
        return json_hash(keys) in self._cache

    def get(self, keys: JSONDict) -> A:
        return self._cache[json_hash(keys)]

    def set(self, keys: JSONDict, value: A):
        self._cache[json_hash(keys)] = value
