# Common Labrea Patterns

## Pattern 1: Simple Dataset Chain

The most basic pattern — datasets that depend on options and on each other.

```python
from labrea import dataset, Option

@dataset
def base_rate(rate: float = Option('RATE')) -> float:
    return rate / 100

@dataset
def adjusted_rate(
    base: float = base_rate,
    adjustment: float = Option('ADJUSTMENT', 0.0)
) -> float:
    return base + adjustment

@dataset
def final_amount(
    principal: float = Option('PRINCIPAL'),
    rate: float = adjusted_rate
) -> float:
    return principal * (1 + rate)

# Evaluate the full chain:
final_amount({'RATE': 5, 'PRINCIPAL': 1000})  # => 1050.0
final_amount({'RATE': 5, 'PRINCIPAL': 1000, 'ADJUSTMENT': 0.01})  # => 1060.0
```

## Pattern 2: Overloading for Environment Switching

Use dispatch to swap implementations based on environment or mode.

```python
@dataset(dispatch='DATA.SOURCE')
def load_customers(path: str = Option('DATA.PATH')) -> list:
    import csv
    with open(path) as f:
        return list(csv.DictReader(f))

@load_customers.overload('DATABASE')
def load_from_db(conn_str: str = Option('DB.CONNECTION')) -> list:
    return query_db(conn_str, 'SELECT * FROM customers')

@load_customers.overload('MOCK')
def mock_customers() -> list:
    return [{'id': 1, 'name': 'Test Customer'}]

# Production:
load_customers({'DATA': {'PATH': '/data/customers.csv'}})

# Testing:
load_customers({'DATA': {'SOURCE': 'MOCK'}})
```

## Pattern 3: Interface for Swappable Subsystems

When you have multiple datasets that must change together, group them in an
interface.

```python
from labrea import interface, implements, abstractdataset, dataset, Option

@interface('STORAGE.BACKEND')
class StorageLayer:
    @abstractdataset
    def read(key: str) -> bytes: ...

    @abstractdataset
    def write(key: str, data: bytes) -> None: ...

    @dataset
    def read_json(
        key: str = Option('KEY'),
        raw: bytes = read.__func__
    ) -> dict:
        import json
        return json.loads(raw)

@implements(StorageLayer, alias='S3')
class S3Storage:
    @staticmethod
    @dataset
    def read(key: str = Option('KEY'), bucket: str = Option('S3.BUCKET')) -> bytes:
        return s3_client.get_object(Bucket=bucket, Key=key)['Body'].read()

    @staticmethod
    @dataset
    def write(
        key: str = Option('KEY'),
        data: bytes = Option('DATA'),
        bucket: str = Option('S3.BUCKET')
    ) -> None:
        s3_client.put_object(Bucket=bucket, Key=key, Body=data)

@implements(StorageLayer, alias='LOCAL')
class LocalStorage:
    @staticmethod
    @dataset
    def read(key: str = Option('KEY'), base: str = Option('LOCAL.PATH')) -> bytes:
        return Path(base, key).read_bytes()

    @staticmethod
    @dataset
    def write(
        key: str = Option('KEY'),
        data: bytes = Option('DATA'),
        base: str = Option('LOCAL.PATH')
    ) -> None:
        Path(base, key).write_bytes(data)

# Downstream code uses interface members directly:
@dataset
def process_record(record: dict = StorageLayer.read_json) -> dict:
    return transform(record)

# Switch implementations via options:
process_record({'STORAGE': {'BACKEND': 'S3'}, 'KEY': 'record.json', 'S3': {'BUCKET': 'my-bucket'}})
process_record({'STORAGE': {'BACKEND': 'LOCAL'}, 'KEY': 'record.json', 'LOCAL': {'PATH': '/data'}})
```

## Pattern 4: Pre-configured Dataset Variants

Create specialized versions of a dataset with some options locked in.

```python
@dataset
def fetch_data(
    url: str = Option('API.URL'),
    timeout: int = Option('API.TIMEOUT', 30)
) -> dict:
    return requests.get(url, timeout=timeout).json()

# Variant with forced timeout:
fast_fetch = fetch_data.with_options({'API': {'TIMEOUT': 5}})

# Variant with default URL (can be overridden):
default_fetch = fetch_data.with_default_options({'API': {'URL': 'https://api.example.com'}})
```

## Pattern 5: Option Namespaces for Package Configuration

Organize all options for a module or package under a namespace.

```python
from labrea import Option

@Option.namespace
class MY_SERVICE:
    class API:
        BASE_URL: str
        KEY: str
        TIMEOUT: int = 30
    class CACHE:
        ENABLED: bool = True
        TTL: int = 3600
    LOG_LEVEL: str = 'INFO'

# Use namespace members as regular Options:
@dataset
def api_client(
    url: str = MY_SERVICE.API.BASE_URL,
    key: str = MY_SERVICE.API.KEY,
    timeout: int = MY_SERVICE.API.TIMEOUT
) -> APIClient:
    return APIClient(url, key, timeout)
```

## Pattern 6: Inline Transformations

Chain transformations using `>>` to build derived evaluatables without writing
full dataset functions.

```python
import json
from labrea import Option

# Parse JSON string from options:
config = Option('RAW_CONFIG') >> json.loads

# Chain multiple transformations:
user_ids = Option('USERS') >> json.loads >> (lambda users: [u['id'] for u in users])

# Transform with a named function:
def normalize(text: str) -> str:
    return text.strip().lower()

clean_name = Option('NAME') >> normalize
```

## Pattern 7: Coalesce for Fallback Chains

Try multiple sources and take the first that succeeds.

```python
from labrea import coalesce, Option, Value

# Try env-specific config, then global config, then default:
db_host = coalesce(
    Option('ENV.DB.HOST'),
    Option('DB.HOST'),
    Value('localhost')
)
```

## Pattern 8: Switch for Conditional Logic

Select an evaluatable based on a runtime value.

```python
from labrea import switch, Option, Value

greeting = switch(
    Option('LANG'),
    {
        'en': Value('Hello'),
        'es': Value('Hola'),
        'fr': Value('Bonjour'),
    },
    default=Value('Hi')
)
```

## Pattern 9: Dataset Class

Use `@datasetclass` for class-based dataset composition where multiple related
values are computed together.

```python
from labrea import datasetclass, Option

@datasetclass
class ModelConfig:
    learning_rate: float = Option('MODEL.LR')
    epochs: int = Option('MODEL.EPOCHS', 10)
    batch_size: int = Option('MODEL.BATCH_SIZE', 32)

config = ModelConfig({'MODEL': {'LR': 0.001}})
config.learning_rate  # => 0.001
config.epochs         # => 10
```

## Pattern 10: Testing Labrea Code

```python
import pytest
from labrea import dataset, Option

@dataset
def process(x: int = Option('X'), y: int = Option('Y')) -> int:
    return x + y

def test_evaluate():
    assert process({'X': 1, 'Y': 2}) == 3

def test_validate():
    process.validate({'X': 1, 'Y': 2})  # passes

    with pytest.raises(KeyNotFoundError):
        process.validate({})  # missing keys

def test_explain():
    assert process.explain() == {'X', 'Y'}

def test_keys():
    assert process.keys({'X': 1, 'Y': 2}) == {'X', 'Y'}

def test_overload():
    @dataset(dispatch='MODE')
    def flexible(x: int = Option('X')) -> int:
        return x

    @flexible.overload('DOUBLE')
    def doubled(x: int = Option('X')) -> int:
        return x * 2

    assert flexible({'X': 5}) == 5
    assert flexible({'X': 5, 'MODE': 'DOUBLE'}) == 10
```

## Anti-patterns to Avoid

### Don't call datasets like regular functions

```python
# WRONG — datasets take an options dict, not keyword arguments
result = my_dataset(x=1, y=2)

# RIGHT
result = my_dataset({'X': 1, 'Y': 2})
```

### Don't mutate the options dictionary

```python
# WRONG
opts = {'X': 1}
opts['X'] = 2
my_dataset(opts)

# RIGHT — create a new dict
opts = {'X': 1}
my_dataset({**opts, 'X': 2})
```

### Don't use mutable defaults without default_factory

```python
# WRONG — same list object shared across evaluations
opt = Option('ITEMS', [])

# RIGHT
opt = Option('ITEMS', default_factory=list)
```

### Don't forget dispatch when adding overloads

```python
# WRONG — will raise ValueError
@dataset
def my_ds() -> int:
    return 0

@my_ds.overload('ALT')  # Error! No dispatch set
def alt() -> int:
    return 1

# RIGHT
@dataset(dispatch='MODE')
def my_ds() -> int:
    return 0

@my_ds.overload('ALT')
def alt() -> int:
    return 1
```

### Don't create circular dependencies

```python
# WRONG — infinite recursion at evaluation time
@dataset
def a(b_val: int = b) -> int:
    return b_val + 1

@dataset
def b(a_val: int = a) -> int:
    return a_val + 1
```
