import uuid

from labrea import abstractdataset, dataset
from labrea.cache import NoCache


@dataset
def cached():
    return str(uuid.uuid4())


@dataset.nocache
def not_cached():
    return str(uuid.uuid4())


@abstractdataset
def abstract():
    ...


@abstract.overload.nocache
def overload():
    pass


not_cached_2 = cached.nocache


def test_cache():
    assert cached({}) == cached({})
    assert not_cached({}) != not_cached({})
    assert not_cached_2({}) != not_cached_2({})

    assert isinstance(overload._cache, NoCache)
