import random

import pytest

import tests.ext.datasets
import tests.pkg.datasets
from labrea import (
    DatasetDict,
    DatasetList,
    Field,
    Option,
    Switch,
    abstractdataset,
    dataset,
    datasetclass,
)
from labrea.cache import NoCache
from labrea.datasets import Overload
from labrea.types import EvaluationError, ValidationError, Value


@datasetclass
class DSC:
    val = Option("DSC.VAL")
    const = Field(0)

    def __eq__(self, other):
        return self.val == other


@dataset
def dependency(dependent_input=Option("DEPENDENT.INPUT")):
    return dependent_input


unwrapped_value = []


@dataset
def tst_dataset(
    x=Option("X", 1),
    y=Switch("Y", {True: 1, False: 2}),
    dsc=DSC,
    dsl=DatasetList(Option("LIST.A"), Option("LIST.B")),
    dsd=DatasetDict({"a": Option("DICT.A"), "b": Option("DICT.B")}),
    val=Value("value"),
    lst=unwrapped_value,
):
    return x, y, dsc, dsl, dsd, val, lst


config = {
    "X": random.random(),
    "Y": random.choice([True, False]),
    "DSC": {"VAL": random.random()},
    "LIST": {
        "A": random.random(),
        "B": random.random(),
    },
    "DICT": {
        "A": random.random(),
        "B": random.random(),
    },
}


def test_dataset():
    x, y, dsc, dsl, dsd, val, lst = tst_dataset(config)

    assert x == config["X"]
    assert 1 if config["Y"] else 2
    assert dsc == config["DSC"]["VAL"]
    assert dsc.const == 0
    assert dsl == list(config["LIST"].values())
    assert dsd == {key.lower(): val for key, val in config["DICT"].items()}
    assert lst == unwrapped_value and lst is not unwrapped_value


def test_validate():
    with pytest.raises(ValidationError):
        tst_dataset.validate({})

    good_config = {k: v for k, v in config.items() if k != "X"}
    tst_dataset.validate(good_config)

    bad_config = {k: v for k, v in good_config.items() if k != "Y"}
    with pytest.raises(ValidationError):
        tst_dataset.validate(bad_config)

    with pytest.raises(EvaluationError):
        tst_dataset.evaluate(bad_config)


def test_warning():
    @dataset
    def x():
        return 1

    with pytest.warns(UserWarning):

        @dataset
        def y():
            return x


def test_no_default():
    with pytest.raises(TypeError):

        @dataset
        def x(y):
            pass


def test_where():
    @dataset.where(a=Option("Y"))
    def x(a=Option("A")):
        return a

    assert x.evaluate({"Y": 1}) == 1
    assert x.where(a=Option("Z")).evaluate({"Z": 2}) == 2

    with pytest.raises(TypeError):
        tests.pkg.datasets.abstract.where(x=1)


def test_overloads():
    overloads = {
        "LABREA": {
            "IMPLEMENTATIONS": {
                "tests": {
                    "pkg": {
                        "datasets": {
                            "basic": "tests.ext.datasets.basic_overload",
                            "abstract": "tests.ext.datasets.abstract_overload",
                        }
                    }
                }
            },
            "REQUIRE": ["tests.ext"],
        },
        "CUSTOM_DISPATCH": "custom_alias_dispatch_overload",
    }

    assert tests.pkg.datasets.basic.evaluate({})
    assert not tests.pkg.datasets.basic.evaluate(overloads)

    assert tests.pkg.datasets.dispatch.evaluate({}) == "default"
    assert tests.pkg.datasets.dispatch.evaluate(overloads) == "overload"

    with pytest.raises(EvaluationError):
        tests.pkg.datasets.abstract.evaluate({})

    assert tests.pkg.datasets.abstract.evaluate(overloads)

    bad_overload = {"CUSTOM_DISPATCH": "does.not.exist"}

    with pytest.warns(UserWarning):
        tests.pkg.datasets.dispatch.evaluate(bad_overload)


def test_repr():
    assert repr(tests.pkg.datasets.basic) == "<Dataset tests.pkg.datasets.basic>"
    assert (
        repr(tests.ext.datasets.basic_overload)
        == "<Overload basic_overload of <Dataset tests.pkg.datasets.basic>>"
    )

    def x():
        pass

    assert repr(Overload(x)) == f"<Unbound Overload {x.__qualname__}>"


def test_decorator_args():
    @dataset(dispatch="DISPATCH", where={"x": Option("X")}, cache=NoCache)
    def y(x=1):
        return x

    @y.overload(where={"x": Option("XX")}, cache=NoCache, alias="y_overload")
    def y_overload(x=1):
        return x

    assert isinstance(y.default._cache, NoCache)
    assert isinstance(y_overload._cache, NoCache)

    assert y.evaluate({"X": 10}) == 10
    assert y.evaluate({"XX": 20, "DISPATCH": "y_overload"}) == 20


def test_abstract_dataset_warnings():
    with pytest.warns(Warning):

        @abstractdataset.nocache
        def x():
            pass

    with pytest.warns(Warning):

        @abstractdataset.where(y=Option("X"))
        def z(y=1):
            return y


def test_complex_dispatch():
    @dataset
    def custom_dispatch() -> str:
        return "overload"

    @abstractdataset.dispatch(dispatch=custom_dispatch)
    def abstract():
        ...

    @abstract.overload(alias="overload")
    def overload():
        return "overload"

    assert abstract({}) == "overload"


def test_custom_callback():
    store = []

    @dataset(callbacks=[lambda val, opts: store.append(val)])
    def x():
        return 1

    x.evaluate({})
    x.evaluate({})

    assert store == [1]  # Only called once because of cache

    store = []

    @dataset.nocache(callbacks=[lambda val, opts: store.append(val)])
    def y():
        return 1

    y.evaluate({})
    y.evaluate({})

    assert store == [1, 1]  # Called every time because of no cache


def test_add_callback():
    store = []

    @dataset
    def x():
        return 1

    x.add_callbacks(lambda val, opts: store.append(val))

    x.evaluate({})
    x.evaluate({})

    assert store == [1]  # Called only once


def test_scoped_options_deco():
    @dataset
    def x(a: int = Option("A")):
        return a

    @dataset(options={"A": 2})
    def y(x: int = x, b: int = Option("B")) -> int:
        return x + b

    assert y({"B": 3}) == 5
    assert y({"A": 3, "B": 3}) == 5


def test_with_options():
    @dataset
    def x(a: int = Option("A")):
        return a

    @dataset
    def y(x: int = x, b: int = Option("B")) -> int:
        return x + b

    z = y.with_options({"A": 2})

    assert z({"B": 3}) == 5
    assert z({"A": 3, "B": 3}) == 5


def test_with_cache():
    @dataset
    def rand():
        return random.random()

    assert rand.evaluate({}) == rand.evaluate({})

    rand_no_cache = rand.with_cache(NoCache)

    assert rand_no_cache.evaluate({}) != rand_no_cache.evaluate({})

    rand.set_cache(NoCache)

    assert rand.evaluate({}) != rand.evaluate({})


def test_distinct_callbacks():
    @dataset
    def x():
        return 1

    @dataset
    def y():
        return 2

    assert x._callbacks is not y._callbacks
