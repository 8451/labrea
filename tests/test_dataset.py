import logging
import pytest
import uuid

from labrea.computation import CallbackEffect
from labrea.dataset import Dataset, dataset, abstractdataset
from labrea.exceptions import EvaluationError
from labrea.logging import LogRequest
from labrea.option import Option
import labrea.runtime
from labrea.types import Evaluatable


def test_dataset():
    @dataset
    def add(a: int = Option('A'), b: int = Option('B')) -> int:
        return a + b

    assert add.evaluate({'A': 1, 'B': 2}) == 3
    add.validate({'A': 1, 'B': 2})
    assert add.keys({'A': 1, 'B': 2}) == {'A', 'B'}
    assert add.explain() == {'A', 'B'}


def test_dataset_non_decorator() -> None:
    a = dataset(Option('A'))
    assert isinstance(a, Dataset)
    assert a.evaluate({'A': 1}) == 1


def test_overloads():
    @dataset(dispatch='X')
    def combine(a: int = Option('A'), b: int = Option('B')) -> int:
        return a + b

    @combine.overload(alias='Y')
    def multiply(a: int = Option('C'), b: int = Option('D')) -> int:
        return a * b

    assert combine.evaluate({'A': 1, 'B': 2}) == 3
    combine.validate({'A': 1, 'B': 2})
    assert combine.keys({'A': 1, 'B': 2}) == {'A', 'B'}
    assert combine.explain() == {'A', 'B'}

    assert multiply.evaluate({'C': 1, 'D': 2}) == 2
    multiply.validate({'C': 1, 'D': 2})
    assert multiply.keys({'C': 1, 'D': 2}) == {'C', 'D'}
    assert multiply.explain() == {'C', 'D'}

    assert combine.evaluate({'X': 'Y', 'C': 1, 'D': 2}) == 2
    combine.validate({'X': 'Y', 'C': 1, 'D': 2})
    assert combine.keys({'X': 'Y', 'C': 1, 'D': 2}) == {'X', 'C', 'D'}
    assert combine.explain({'X': 'Y'}) == {'X', 'C', 'D'}

    assert combine.evaluate({'X': 'Z', 'A': 1, 'B': 2}) == 3
    combine.validate({'X': 'Z', 'A': 1, 'B': 2})
    assert combine.keys({'X': 'Z', 'A': 1, 'B': 2}) == {'A', 'B'}
    assert combine.explain({'X': 'Z'}) == {'A', 'B'}


def test_overload_no_dispatch():
    @dataset
    def x():
        pass

    with pytest.raises(ValueError):
        @x.overload('A')
        def y():
            pass


def test_abstract():

    @abstractdataset(dispatch='A')
    def x() -> int:
        pass

    @x.overload('B')
    def y() -> int:
        return 1

    with pytest.raises(EvaluationError):
        x()

    assert x.evaluate({'A': 'B'}) == 1


def test_repr():
    def add(a: int = Option('A'), b: int = Option('B')) -> int:
        return a + b

    assert repr(dataset(add)) == f"<Dataset {add.__qualname__}>"


def test_cache():
    @dataset
    def uuid4() -> uuid.UUID:
        return uuid.uuid4()

    assert uuid4() == uuid4()


def test_nocache():
    @dataset.nocache
    def uuid4() -> uuid.UUID:
        return uuid.uuid4()

    assert uuid4() != uuid4()


def test_effect():
    store = None

    def set_store(value):
        nonlocal store
        store = value
        return value

    @dataset.nocache(effects=[CallbackEffect(set_store)])
    def uuid4() -> uuid.UUID:
        return uuid.uuid4()

    result = uuid4()
    assert store == result

    @dataset.nocache(effects=[set_store])
    def uuid4() -> uuid.UUID:
        return uuid.uuid4()

    result = uuid4()
    assert store == result

    @dataset.nocache
    def uuid4() -> uuid.UUID:
        return uuid.uuid4()

    uuid4.add_effect(CallbackEffect(set_store))
    result = uuid4()
    assert store == result

    result = uuid4()
    assert store == result

    @dataset.nocache(effects=[set_store])
    def uuid4() -> uuid.UUID:
        return uuid.uuid4()

    result1 = uuid4()
    assert store == result1

    uuid4.disable_effects()
    result2 = uuid4()
    assert store != result2

    uuid4.enable_effects()
    result3 = uuid4()
    assert store == result3

    result4 = uuid4({'LABREA': {'EFFECTS': {'DISABLED': True}}})
    assert store != result4


def test_set_dispatch():
    @dataset
    def x() -> int:
        return 1

    x.set_dispatch(Option('A'))

    @x.overload('A')
    def y() -> int:
        return 2

    assert x() == 1
    assert x.evaluate({'A': 'A'}) == 2


def test_where():
    def add(x: int, y: int) -> int:
        return x + y

    add = dataset.where(x=Option('X'), y=Option('Y')).wrap(add)

    assert add.evaluate({'X': 1, 'Y': 2}) == 3
    add.validate({'X': 1, 'Y': 2})
    assert add.keys({'X': 1, 'Y': 2}) == {'X', 'Y'}
    assert add.explain() == {'X', 'Y'}


def test_force_options():
    @dataset(options={'A': 1})
    def x(a: int = Option('A'), b: int = Option('B')) -> int:
        return a + b

    assert x({'B': 2}) == x({'A': 2, 'B': 2}) == 3
    x.validate({'B': 2})
    assert x.keys({'B': 2}) == {'B'}
    assert x.explain() == {'B'}

    with pytest.raises(EvaluationError):
        x()
    with pytest.raises(EvaluationError):
        x.validate({})
    with pytest.raises(EvaluationError):
        x.keys({})


def test_default_options():
    @dataset(default_options={'A': 1})
    def x(a: int = Option('A'), b: int = Option('B')) -> int:
        return a + b

    assert x({'B': 2}) == 3
    x.validate({'B': 2})
    assert x.keys({'B': 2}) == {'B'}
    assert x.explain() == {'B'}

    assert x({'A': 2, 'B': 2}) == 4
    x.validate({'A': 2, 'B': 2})
    assert x.keys({'A': 2, 'B': 2}) == {'A', 'B'}
    assert x.explain({'A': 2}) == {'A', 'B'}

    with pytest.raises(EvaluationError):
        x()
    with pytest.raises(EvaluationError):
        x.validate({})
    with pytest.raises(EvaluationError):
        x.keys({})


def test_default():
    @dataset(dispatch='X')
    def x() -> str:
        return 'x'

    @x.overload('Y')
    def y() -> str:
        return 'y'

    assert x.default({'X': 'Y'}) == 'x'


def test_with_options():
    @dataset
    def x(a: int = Option('A'), b: int = Option('B')) -> int:
        return a + b

    x1 = x.with_options({'A': 1})
    x2 = x.with_options({'A': 2})

    assert isinstance(x1, type(x))

    assert x1({'B': 2}) == 3
    assert x2({'B': 2}) == 4


def test_with_default_options():
    @dataset
    def x(a: int = Option('A'), b: int = Option('B')) -> int:
        return a + b

    x1 = x.with_default_options({'A': 1})

    assert isinstance(x1, type(x))

    assert x1({'B': 2}) == 3
    assert x1({'A': 2, 'B': 2}) == 4


def test_logging():
    @dataset
    def x() -> int:
        return 1

    handler_run = False

    def test_logging_handler(request: LogRequest) -> None:
        nonlocal handler_run
        handler_run = True
        assert request.level == logging.INFO
        assert request.name == x.__module__
        assert request.msg == f'Labrea: Evaluating {x!r}'

    with labrea.runtime.handle(LogRequest, test_logging_handler):
        x()

    assert handler_run
