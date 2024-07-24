# Usage

Labrea exposes a declarative way to define the data that your application uses,
the relationships between different datasets, and the user inputs necessary for
those datasets.


## Motivation

Imagine that you have a csv file that contains a list of stores, their regions,
and their total sales across multiple days, where each day is a different row.
You read in the csv as a Pandas dataframe, and then in different parts of your 
program you need the set of distinct store codes, the distinct regions, and
the date range captured by the file. You write functions like so to read in the
data and derive these values.

```python
from typing import Set, Tuple
import datetime
import pandas as pd

def read_input(path: str) -> pd.DataFrame:
    return pd.read_csv(path)

def get_distinct_stores(data: pd.DataFrame) -> Set[str]:
    return set(data['store_id'])

def get_distinct_regions(data: pd.DataFrame) -> Set[str]:
    return set(data['region_id'])

def get_min_date(data: pd.DataFrame) -> datetime.date:
    return min(data['date'])

def get_max_date(data: pd.DataFrame) -> datetime.date:
    return max(data['date'])

def get_date_range(data: pd.DataFrame) -> Tuple[datetime.date, datetime.date]:
    return get_min_date(data), get_max_date(data)
```

This is ok, but there is a subtle problem with the way this is written. Each of 
our `get_*` functions are all designed to use the output of read_input, but there
is no explicit dependency being declared anywhere. The only way to know that
`get_distinct_stores` should take the output of `read_input` is through comments. 
As an application grows, these kinds of implicit dependencies can lead to a lack 
of maintainability and bugs that are hard to identify the cause of.

One option would be to move the `read_input` call inside each of our `get_*` 
functions, like so:

```python
from typing import Set
import pandas as pd

def read_input(path: str) -> pd.DataFrame:
    return pd.read_csv(path)

def get_distinct_stores(path: str) -> Set[str]:
    return set(read_input(path)['store_id'])

def get_distinct_regions(path: str) -> Set[str]:
    return set(read_input(path)['region_id'])

...
```

This helps make our dependencies more clear, but at the cost of greatly increased
coupling. Imagine we change `read_input` to take a `fmt` parameter, which specifies
if the file is a csv or an excel file. We would have to add that `fmt` parameter 
to the signature of *every* one of our `get_*` functions, which greatly hurts
maintainability. Additionally, the performance of our code took a hit because
the inputs are being read in every time read_input is called, even though it's
the same data being used in each `get_*` call.

## Datasets

The way Labrea handles this is with `Dataset`s. A `Dataset` is a defined as a
function that takes some input parameters (called `Option`s), and has explicit
dependencies on other datasets. When the dataset is created (by passing a 
config dictionary of `Option`s), all the dependencies are resolved automatically
for you. 

This is how we would handle our problem from before using Labrea.

```python
from typing import Set, Tuple
import datetime

import pandas as pd

from labrea import dataset, Option


@dataset
def input_data(path: str = Option('INPUT.PATH')) -> pd.DataFrame:
    return pd.read_csv(path)

@dataset
def distinct_stores(data: pd.DataFrame = input_data) -> Set[str]:
    return set(data['store_id'])

@dataset
def distinct_regions(data: pd.DataFrame = input_data) -> Set[str]:
    return set(data['region_id'])

@dataset
def min_date(data: pd.DataFrame = input_data) -> datetime.date:
    return min(data['date'])

@dataset
def max_date(data: pd.DataFrame = input_data) -> datetime.date:
    return max(data['date'])

@dataset
def date_range(
        min_date: datetime.date = min_date, 
        max_date: datetime.date = max_date
) -> Tuple[datetime.date, datetime.date]:
    return min_date, max_date


options = {
    'INPUT': {
        'PATH': '/path/to/input.csv'
    }
}

distinct_regions(options) == {'014', '620', '706'} 
```

All of our functions have been converted into `Dataset`s using the `@dataset` 
decorator. The inputs to our functions all have defaults which are either 
`Option`s, or other `Dataset`s. These `Dataset`s take a dictionary of options as
their input, extract the necessary options using the `Option`s, and recursively 
calculate any dependent datasets before calling the body of the function. 

This allows us to decouple the implementations of each of our functions, while
also explicitly declaring any dependencies from one piece of data to the next.
It also helps with our issue of upstream dependencies taking new arguments. If
we wanted to take that `fmt` argument in `input_data`, we can add it like so,
with no impact to the rest of our datasets.

```python
from typing import Set

import pandas as pd

from labrea import dataset, Option


@dataset
def input_data(
        path: str = Option('INPUT.PATH'),
        fmt: str = Option('INPUT.FMT', 'csv')
) -> pd.DataFrame:
    if fmt == 'csv':
        return pd.read_csv(path)
    elif fmt == 'excel':
        return pd.read_excel(path)
    else:
        raise ValueError('Only csv and excel files are accepted.')

@dataset
def distinct_stores(data: pd.DataFrame = input_data) -> Set[str]:
    return set(data['store_id'])

@dataset
def distinct_regions(data: pd.DataFrame = input_data) -> Set[str]:
    return set(data['region_id'])


options = {
    'INPUT': {
        'PATH': '/path/to/input.xlsx',
        'FMT': 'excel'
    }
}

distinct_regions(options) == {'014', '620', '706'} 
```

## Additional Features

### Caching Results

By default, when a dataset is evaluated with some inputs the result is cached
in memory, so if the same inputs are provided it does not need to be 
recalculated. This might be undesirable (for example if your dataset should
return random data on each call); you can disable this using the 
`@dataset.nocache` decorator. 


```python
import random

from labrea import dataset, Option


@dataset
def same_random_number_every_time(
        minimum: float = Option('MIN'),
        maximum: float = Option('MAX')
):
  return random.random() * (maximum - minimum) + minimum


@dataset.nocache
def new_random_number_every_time(
        minimum: float = Option('MIN'),
        maximum: float = Option('MAX')
):
  return random.random() * (maximum - minimum) + minimum


config = {
    'MIN': 1,
    'MAX': 2
}

same_random_number_every_time(config)  ## 1.8286543357828648
same_random_number_every_time(config)  ## 1.8286543357828648

new_random_number_every_time(config)  ## 1.226523659380299
new_random_number_every_time(config)  ## 1.907915105351007
```

### Default Values to Options

Options can take a default value. If the value is a string, you can use
[confectioner](https://github.com/8451/confectioner)-style templating syntax to impute
a default based on other config entries.

```python
from labrea import Option

config = {
    'A': 'a',
    'V': 'b'
}

Option('X', 1)(config)          ## 1
Option('Y', '{A}/{V}')(config)  ## 'a/b'
```

### Switches

Sometimes your dataset might have different dependencies depending on some 
input parameter or other condition. We can express this simply using `switch`es.

In this example, we have different logic for cloud vs on-prem, and can 
express that this way. `switch` takes a string representing the option we want
to switch over, a dictionary mapping config values to corresponding datasets,
and (optionally) a default value if the config value is missing or does not 
appear in our mapping.

```python
from labrea import dataset, switch


@dataset
def cloud_inputs():
    ...


@dataset
def onprem_inputs():
    ...


@dataset
def final_data(
        inputs = switch(
            'ENVIRONMENT',
            {
                'CLOUD': cloud_inputs,
                'ONPREM': onprem_inputs
            }
        )
):
    ...


final_data({'ENVIRONMENT': 'CLOUD'})  ## uses cloud_inputs as inputs arg
final_data({'ENVIRONMENT': 'ONPREM'})  ## uses onprem_inputs as inputs arg
```

The first argument to `switch` can also be another dataset. In this example, we
could automatically determine the environment in another dataset rather than 
pass it explicitly in the config.

```python
from labrea import dataset, switch


@dataset
def inferred_environment():
    ...


@dataset
def final_data(
        inputs = switch(
            inferred_environment,
            {
                'CLOUD': cloud_inputs,
                'ONPREM': onprem_inputs
            }
        )
):
    ...
```

### Coalesce
`Coalesce` allows you to provide a sequence of `Dataset`s (or `Option`s, `Switch`es, etc.), and use
the first one that can evaluate. 

```python
from labrea import Coalesce, Option

x = Coalesce(Option('A'), Option('V'), Option('C'))

x({'A': 1}) == 1
x({'V': 2}) == 2
x({'C': 3}) == 3
x({'A': 1, 'V': 2}) == 1
x({'V': 2, 'C': 3}) == 2
x()  ## EvaluationError


y = Coalesce(Option('A'), Option('V'), None)
y({'A': 1}) == 1
y({'V': 2}) == 2
y({'A': 1, 'V': 2}) == 1
y() is None
```

### Overloads
You can write multiple implementations to the same dataset using the `.overload` method of the dataset.
For example, if you want to write a unit test where you mock up reading in some external data, you
could write an overload that provides mock data. 

```python
from typing import List

from labrea import dataset, Option


@dataset(dispatch='INPUT.SOURCE')
def input_data(
        path: str = Option('INPUT.PATH')
) -> List[str]:
    with open(path) as file:
        return file.readlines()


@input_data.overload(alias='MOCK')
def mock_input_data() -> List[str]:
    return ['a', 'b', 'c']
```

Now, we can control which implementation is used by setting the `INPUT.SOURCE` option in our config.
By default, if nothing is provided, we use the default implementation in the body of `input_data`.

```python
input_data({'INPUT': {'PATH': '/input/data/path'}})  ## Use default implementation
input_data({'INPUT': {'SOURCE': 'MOCK'}}) == ['a', 'b', 'c'] 
input_data({'INPUT': {'SOURCE': 'UNKNOWN_SOURCE'}})  ## Error
```

#### Abstract Datasets
We can also have datasets that have no default implementation, called abstract datasets.

```python
from typing import List

from labrea import abstractdataset, Option

@abstractdataset(dispatch='INPUT.SOURCE')
def input_data() -> List[str]:
    ...


@input_data.overload(alias='FLAT_FILE')
def flat_file_input_data(
        path: str = Option('INPUT.PATH')
) -> List[str]:
    with open(path) as file:
        return file.readlines()


@input_data.overload(alias='MOCK')
def mock_input_data() -> List[str]:
    return ['a', 'b', 'c']
```

### Interfaces
We can write collections of multiple datasets whose implementations are connected using interfaces.
For example, you may want your application to pull from a SQL database in production, but from a CSV 
file in development. You can define an interface that specifies the datasets that need to be implemented,
and then provide different implementations for each environment.

#### Interface Definition
```python
import pandas as pd
from labrea import abstractdataset, dataset, interface, Option

@interface(dispatch='ENVIRONMENT')
class DataSource:
    @staticmethod  # Adding staticmethod appeases linters/IDEs that don't understand interfaces
    @abstractdataset
    def store() -> pd.DataFrame:
        """Returns a dataframe of store data."""

    @staticmethod
    @abstractdataset
    def region() -> pd.DataFrame:
        """Returns a dataframe of region data."""

    @staticmethod
    @dataset
    def store_ids(
            store_: pd.DataFrame = store.__func__  # Use .__func__ to refer to the abstract dataset itself
    ) -> set[str]:
        """Derives the set of store ids from the store dataframe. This implementation is shared across all environments
        by default, but can be overridden if necessary."""
        return set(store_['store_id'])

    @staticmethod
    @dataset
    def region_ids(
            region_: pd.DataFrame = region.__func__
    ) -> set[str]:
        return set(region_['region_id'])
```

#### Development Implementation
```python
@DataSource.implementation(alias='DEVELOPMENT')
class DevDataSource:
    @staticmethod
    @dataset
    def store(
            path: str = Option('DEV.STORE.PATH')
    ) -> pd.DataFrame:
        return pd.read_csv(path)

    @staticmethod
    @dataset
    def region(
            path: str = Option('DEV.REGION.PATH')
    ) -> pd.DataFrame:
        return pd.read_csv(path)
```

#### Production Implementation
```python
def open_connection(connection_string: str):
    ...


@DataSource.implementation(alias='PRODUCTION')
class ProdDataSource:
    @staticmethod
    @dataset
    def store(
            connection_string: str = Option('PROD.CONNECTION_STRING')
    ) -> pd.DataFrame:
        with open_connection(connection_string) as conn:
            return pd.read_sql('SELECT * FROM stores', conn)

    @staticmethod
    @dataset
    def region(
            connection_string: str = Option('PROD.CONNECTION_STRING')
    ) -> pd.DataFrame:
        with open_connection(connection_string) as conn:
            return pd.read_sql('SELECT * FROM regions', conn)
```

Now, in your code, you can use `DataSource.store` and `DataSource.region` like normal datasets, and
the implementation will be chosen based on the `ENVIRONMENT` option in your config.

```python
@dataset
def num_stores(
        store_ids: set[str] = DataSource.store_ids
) -> int:
    return len(store_ids)
```

### Collections

Labrea provides a few helper functions for creating collections of datasets. For example,
you might have a list of datasets that you want to provide as a single input to another
dataset. You can use the `evaluatable_list` function to accomplist this.

```python
from labrea import evaluatable_list, dataset

@dataset
def x() -> int:
    return 1

@dataset
def y() -> int:
    return 2

@dataset
def z(
        x_and_y: list[int] = evaluatable_list(x, y)
) -> list[int]:
    return x_and_y


z() == [1, 2]
```

The `evaluatable_tuple` and `evaluatable_set` functions work similarly. There is also a `evaluatable_dict`
function that takes a dictionary mapping (static) keys to labrea objects.

```python
from labrea import evaluatable_dict

@dataset
def z(
        xy_dict: dict[str, int] = evaluatable_dict({'x': x, 'y': y})
) -> dict[str, int]:
    return xy_dict

z() == {'x': 1, 'y': 2}
```

### Map
Sometimes you want to use a dataset multiple times with different options. This can be accomplished using the
`Map` type. `Map` takes a dataset and a dictionary mapping option keys to labrea objects that return lists
(or other iterables) of values. When the `Map` object is evaluated, it will call the dataset with each of the
values in the dictionary, and return an iterable of tuples, where the first element is the options set on that 
iteration, and the second element is the value. Like the build-in `map`, this iterable is lazy and is not a 
list.

```python
from labrea import dataset, Option, Map


@dataset
def x_plus_y(
        x: int = Option('X'),
        y: int = Option('Y')
) -> int:
    return x + y


mapped = Map(x_plus_y, {'X': Option('X_LIST')})

for keys, value in mapped({'X_LIST': [1, 2, 3], 'Y': 10}):
    print(keys, value)

## {'X': 1} 11
## {'X': 2} 12
## {'X': 3} 13
```

`Map` objects have a `.values` property that can be used to only get the values.

```python
for value in mapped.values({'X_LIST': [1, 2, 3], 'Y': 10}):
    print(value)
    
## 11
## 12
## 13
```

### In-Line Transformations
Sometimes you want to perform a transformation on a dataset (or other object) that is not worth creating 
a new dataset for. A common example is an Option that you want to parse as a date. You can use the
`>>` operator (or the equivalent `.apply()` method) to perform this transformation in-line. The `>>`
operator is shared by all Labrea objects.

```python
from labrea import Option
import datetime as dt

start_date = Option('START_DATE') >> dt.datetime.fromisoformat

start_date({'START_DATE': '2022-01-01'}) == dt.datetime(2022, 1, 1)
```

### Pipelines
Labrea datasets are really useful when you know the dependency tree in advance. However, sometimes 
you want to write code that performs some transformation on an arbitrary input, and perhaps you want 
to perform a series of these transformations in an arbitrary order. To accomplish this, Labrea exposes
a `Pipeline` class, where each step is created using the `@pipeline_step` decorator. 

Pipelines look similar to datasets, but their first argument is always the input to the pipeline, and
should not have a default value. To combine pipeline steps into a pipeline, use the `+` operator. Pipelines
can be evaluated like a dataset, and it will return a function of 1 variable. If you want to run the pipeline
on a value, use the `.transform(input, options)` method.

For example, if you were building a feature engineering pipeline, you could write a series of functions
that take a dataframe and add new columns, and then chain different subsets of these functions together
to create different feature sets.

```python
import pandas as pd
from labrea import pipeline_step, Option, dataset

@dataset
def store_sales(path: str = Option('PATH.STORE_SALES')) -> pd.DataFrame:
    pd.read_csv(path)

@dataset
def store_square_footage(path: str = Option('PATH.STORE_SQFT')) -> pd.DataFrame:
    pd.read_csv(path)


@pipeline_step
def add_sales(
        df: pd.DataFrame,
        sales: pd.DataFrame = store_sales
) -> pd.DataFrame:
    return pd.merge(df, sales, on='store_id', how='left')


@pipeline_step
def add_square_footage(
        df: pd.DataFrame,
        sqft: pd.DataFrame = store_square_footage
) -> pd.DataFrame:
    return pd.merge(df, sqft, on='store_id', how='left')


@pipeline_step
def add_sales_per_sqft(
        df: pd.DataFrame,
        sales: pd.DataFrame = store_sales,
        sqft: pd.DataFrame = store_square_footage
) -> pd.DataFrame:
    df = pd.merge(df, sales, on='store_id', how='left')
    df = pd.merge(df, sqft, on='store_id', how='left')
    df['sales_per_sqft'] = df['sales'] / df['sqft']
    return df.drop(columns=['sales', 'sqft'])


basic_features = add_sales + add_square_footage
derived_features = add_sales_per_sqft
all_features = basic_features + derived_features


stores = pd.read_csv('/path/to/stores.csv')
options = {
    'PATH.STORE_SALES': '/path/to/store_sales.csv',
    'PATH.STORE_SQFT': '/path/to/store_sqft.csv'
}

basic_features.transform(stores, options)
## Returns a dataframe with columns from stores and new columns sales and sqft

derived_features.transform(stores, options)
## Returns a dataframe with columns from stores and a new column sales_per_sqft

all_features.transform(stores, options)
## Returns a dataframe with columns from stores and new columns sales, sqft, and sales_per_sqft
```

Pipelines can also be used as inline transformations on other Labrea objects.

```python
from labrea import dataset, Option, pipeline_step

@dataset
def letters() -> list[str]:
    return ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j']


@pipeline_step
def take_first_n(
        lst: list[str],
        n: int = Option('N')
) -> list[str]:
    return lst[:n]


first_n_letters = letters >> take_first_n

first_n_letters({'N': 3}) == ['a', 'b', 'c']
```

### Helper Pipelines
Labrea provides a few helper functions for creating common pipeline steps. These are
`map`, `filter`, and `reduce`, all under the `labrea.functions` module.

```python
from labrea import dataset
import labrea.functions as lf

@dataset
def numbers() -> list[int]:
    return [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]

sum_squared_evens = (
        numbers >> 
        lf.filter(lambda x: x % 2 == 0) >> 
        lf.map(lambda x: x**2) >> 
        lf.reduce(lambda x, y: x + y)
)

sum_squared_evens() == 220
```


### Templates

Similar to the built-in f-strings, Labrea provides a `Template` type for
string interpolation. This can be useful for creating strings that depend on
config values, or for creating strings that depend on the results of other
datasets.

```python
from labrea import dataset, Option, Template

@dataset
def b_dataset(
        b: str = Option('B')
) -> str:
    return b

template = Template(
    '{A} {:b:}',
    b=b_dataset
)

template({'A': 'Hello', 'B': 'World!'})  ## 'Hello World!'
```

### Dataset Classes

You may want to write classes with more complex behavior that use datasets
and options as their inputs. Similar to the built-in dataclasses, we can use
the `@datasetclass` decorator to create a class whose `__init__` method takes
an options dictionary and automatically evaluates dependencies like a dataset.

```python
from typing import Set

import pandas as pd

from labrea import dataset, datasetclass, Option

@dataset
def input_data(
        path: str = Option('INPUT.PATH'),
        fmt: str = Option('INPUT.FMT', 'csv')
) -> pd.DataFrame:
    if fmt == 'csv':
        return pd.read_csv(path)
    elif fmt == 'excel':
        return pd.read_excel(path)
    else:
        raise ValueError('Only csv and excel files are accepted.')

@dataset
def distinct_stores(data: pd.DataFrame = input_data) -> Set[str]:
    return set(data['store_id'])

@dataset
def distinct_regions(data: pd.DataFrame = input_data) -> Set[str]:
    return set(data['region_id'])


gi

options = {
    'INPUT.PATH': '/path/to/input.xlsx',
    'INPUT.FMT': 'excel'
}

my_data = MyClass(options)

my_data.regions == {'region_1', 'region_2', 'region_3'} 
my_data.lookup_store('<my_store>') == pd.DataFrame(...)
```

### Typing

By default, labrea code is not going to pass a type checker (like MyPy) since 
the default arguments to datasets do not match the type annotations. For example:

```python
from labrea import dataset, Option


@dataset
def add(
        x: int = Option('X'),
        y: int = Option('Y')
) -> int:
    return x + y
```

This will fail a type check because `Option('X')` is not an `int`, it's an
`Option` object. However, when defining datasets, we can appease the type checker
by adding `.result` to the end of all of our `Option`s like so:

```python
from labrea import dataset, Option


@dataset
def add(
        x: int = Option('X').result,
        y: int = Option('Y').result
) -> int:
    return x + y
```

This will signal to the type checker that `Option('X').result` should be treated
as the resulting value of the `Option`, rather than the option value itself.

The `.result` property is shared among all Labrea types (`Option`, `Dataset`,
etc.). Whenever you are defining a dataset or DatasetClass, use the `.result` 
suffix on all your dependencies to pass type checking.


#### Subscripting

For `Option`s, you can explicitly tell the type checker what the resulting
type should be using `Option[<type>](...).result` syntax. This can be useful
if you want to share options across datasets and ensure that the types all
match.

```python
from labrea import dataset, Option

X = Option[int]('X')


## PASSES
@dataset
def double(
        x: int = X.result
) -> int:
    return 2*x

## PASSES
@dataset
def halve(
        x: int = X.result
) -> float:
    return x/2.0

## FAILS
@dataset
def first_char(
        x: str = X.result
) -> str:
    return x[0]
```

#### MyPy Plugin

MyPy has trouble understanding the way the decorators for interfaces and dataset classes work.
A MyPy plugin is provided to help with this. To use it, add the following to your `mypy.ini` file:


```
[mypy]
plugins = labrea.mypy.plugin
```
