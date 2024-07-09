from typing import List
import uuid

import pytest

from confectioner.templating import set_dotted_key

from labrea.application import FunctionApplication
from labrea.cache import cached, NoCache
from labrea.option import Option
import labrea.cache


def test_cached():
    uuid4 = FunctionApplication(uuid.uuid4)
    cached_uuid4 = cached(uuid4)

    assert uuid4() != uuid4()
    assert cached_uuid4() == cached_uuid4()


def test_nocache():
    uuid4 = FunctionApplication(uuid.uuid4)
    cached_uuid4 = cached(uuid4, NoCache())

    assert uuid4() != uuid4()
    assert cached_uuid4() != cached_uuid4()


def test_cached_decorator():
    @cached
    @FunctionApplication.lift
    def uuid4_list(n: int = Option('N')) -> List[uuid.UUID]:
        return [uuid.uuid4() for _ in range(n)]

    assert uuid4_list({'N': 3}) == uuid4_list({'N': 3})
    assert uuid4_list({'N': 3}) != uuid4_list({'N': 4})

    @cached(NoCache())
    @FunctionApplication.lift
    def uuid4_list(n: int = Option('N')) -> List[uuid.UUID]:
        return [uuid.uuid4() for _ in range(n)]


@pytest.mark.parametrize('method', ['ctx', 'LABREA.CACHE.DISABLED', 'LABREA.CACHE.DISABLE'])
def test_disable_cache(method):
    uuid4 = cached(FunctionApplication(uuid.uuid4))

    a = uuid4()
    b = uuid4()

    if method == 'ctx':
        with labrea.cache.disabled():
            c = uuid4()
            d = uuid4()
    else:
        options = {}
        set_dotted_key(method, True, options)
        c = uuid4(options)
        d = uuid4(options)

    e = uuid4()

    assert a == b == e
    assert a != c and c != d
