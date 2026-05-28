# Labrea Advanced Features

## Pipelines

Pipeline steps are composable transformations. Unlike datasets, the first parameter
is the value to transform (no default), and remaining parameters are resolved from
options.

```python
from labrea import pipeline_step, Option

@pipeline_step
def normalize(text: str) -> str:
    return text.strip().lower()

@pipeline_step
def truncate(text: str, max_len: int = Option('MAX_LEN', 100)) -> str:
    return text[:max_len]

@pipeline_step
def prefix(text: str, pfx: str = Option('PREFIX', '')) -> str:
    return f"{pfx}{text}"

# Compose with + operator:
pipeline = normalize + truncate + prefix

# Use .transform() to apply:
pipeline.transform('  HELLO WORLD  ', {'MAX_LEN': 5, 'PREFIX': '> '})
# => '> hello'

# Pipelines are also Evaluatables (they evaluate to functions):
func = pipeline({'MAX_LEN': 5})  # => Callable[[str], str]
func('  HELLO  ')  # => 'hello'
```

### Built-in Pipeline Helpers

```python
from labrea.pipeline import map, filter, reduce, flatten, flatmap

# map: apply a function to each element
doubled = map(lambda x: x * 2)
doubled.transform([1, 2, 3], {})  # => [2, 4, 6]

# filter: keep elements matching predicate
evens = filter(lambda x: x % 2 == 0)
evens.transform([1, 2, 3, 4], {})  # => [2, 4]

# reduce: fold elements
total = reduce(lambda a, b: a + b)
total.transform([1, 2, 3], {})  # => 6

# flatten: flatten nested lists
flat = flatten()
flat.transform([[1, 2], [3, 4]], {})  # => [1, 2, 3, 4]

# Compose with other steps:
process = map(lambda x: x ** 2) + filter(lambda x: x > 5)
process.transform([1, 2, 3, 4], {})  # => [9, 16]
```

### Using Pipelines with Datasets

The `callback` parameter applies a pipeline to a dataset's result:

```python
@dataset(callback=normalize + truncate)
def user_input(text: str = Option('INPUT')) -> str:
    return text

user_input({'INPUT': '  HELLO WORLD  ', 'MAX_LEN': 5})  # => 'hello'
```

## Templates

Templates interpolate option values into strings using confectioner syntax.

```python
from labrea import Template

# Basic interpolation:
url = Template('{API.BASE}/{API.VERSION}/users')
url({'API': {'BASE': 'https://api.example.com', 'VERSION': 'v2'}})
# => 'https://api.example.com/v2/users'

# With parameters (using :name: syntax):
endpoint = Template('{API.BASE}/{:path:}', path='users')
endpoint({'API': {'BASE': 'https://api.example.com'}})
# => 'https://api.example.com/users'
```

Templates can be used as Option defaults:

```python
# The default is a template string, not a plain string:
log_file = Option('LOG.FILE', '{LOG.DIR}/{APP.NAME}.log')
log_file({'LOG': {'DIR': '/var/log'}, 'APP': {'NAME': 'myapp'}})
# => '/var/log/myapp.log'
```

## Effects

Effects are side effects that run after a dataset evaluates. They receive the
computed value but don't change it.

```python
from labrea import dataset, Option
from labrea.computation import Effect, CallbackEffect, ChainedEffect

# Simple callback effect:
@dataset(effects=[lambda val: print(f"Computed: {val}")])
def my_dataset(x: int = Option('X')) -> int:
    return x * 2

# Custom Effect class:
class LogEffect(Effect[int]):
    def run(self, value: int, options) -> int:
        logger.info(f"Result: {value}")
        return value

@dataset(effects=[LogEffect()])
def logged_dataset(x: int = Option('X')) -> int:
    return x * 2

# Add effects to existing datasets:
my_dataset.add_effects(lambda v: audit_log(v))

# Disable/enable effects (useful for testing):
my_dataset.disable_effects()
my_dataset.enable_effects()
```

Effects can also be disabled globally via the `LABREA.EFFECTS.DISABLED` option.

## Caching

### Default: MemoryCache

Datasets are cached in memory by default. The cache key is a fingerprint of
the option values the dataset reads.

```python
@dataset
def expensive(x: int = Option('X')) -> int:
    print("Computing...")
    return x * 2

expensive({'X': 5})  # prints "Computing...", returns 10
expensive({'X': 5})  # returns 10 (cached, no print)
expensive({'X': 6})  # prints "Computing...", returns 12 (different key)
```

### NoCache

```python
@dataset.nocache
def always_fresh() -> float:
    return time.time()
```

### Custom Cache

```python
from labrea.cache import Cache, cached

class RedisCache(Cache):
    def __contains__(self, key: bytes) -> bool: ...
    def __getitem__(self, key: bytes): ...
    def __setitem__(self, key: bytes, value): ...

@dataset
def my_dataset(x: int = Option('X')) -> int:
    return x

my_dataset.set_cache(RedisCache())
```

## Runtime and Request System

The Runtime system provides an extensible handler mechanism for intercepting
and customizing evaluation behavior.

```python
from labrea.runtime import Runtime, Request

# Define a custom request type:
class NotifyRequest(Request[None]):
    def __init__(self, message: str):
        self.message = message

# Register a default handler:
@NotifyRequest.handle
def handle_notify(req: NotifyRequest) -> None:
    print(req.message)

# Use in code:
NotifyRequest("Hello").run()  # prints "Hello"

# Override handlers in a runtime context:
def custom_handler(req: NotifyRequest) -> None:
    send_slack(req.message)

with Runtime({NotifyRequest: custom_handler}):
    NotifyRequest("Hello").run()  # sends to Slack instead
```

All core labrea operations (`evaluate`, `validate`, `keys`, `explain`) go through
the Request system, so they can be intercepted:

```python
from labrea.types import EvaluateRequest

# Log every evaluation:
original = EvaluateRequest._handler

def logging_handler(req: EvaluateRequest):
    print(f"Evaluating: {req.evaluatable!r}")
    return original(req)

with Runtime({EvaluateRequest: logging_handler}):
    my_dataset({'X': 1})
```

## Helper Functions (`labrea.functions`)

The `labrea.functions` module provides 40+ composable functions that return
pipeline steps or can be used with `>>`.

### Math

```python
from labrea.functions import add, subtract, multiply, divide_by, negate, modulo

doubled = Option('X') >> multiply(2)
offset = Option('X') >> add(10)
```

### Comparisons and Predicates

```python
from labrea.functions import eq, gt, lt, positive, is_none, is_in

is_adult = Option('AGE') >> gt(18)
is_valid = Option('STATUS') >> is_in(['active', 'pending'])
```

### Collections

```python
from labrea.functions import flatten, concat, append, length, map_values

items = Option('NESTED') >> flatten
count = Option('ITEMS') >> length
```

### Utilities

```python
from labrea.functions import partial, into, get, get_attribute, call_method, ensure

# get: extract a key from a dict result
name = my_dataset >> get('name')

# get_attribute: get an attribute from an object
attr = my_dataset >> get_attribute('value')

# call_method: call a method on the result
upper = Option('NAME') >> call_method('upper')

# into: construct an object from the result
from datetime import datetime
dt = Option('TIMESTAMP') >> into(datetime.fromtimestamp)
```

## DatasetClass

`@datasetclass` is similar to `@dataclass` but evaluates annotated members from
options at construction time.

```python
from labrea import datasetclass, Option, dataset

@datasetclass
class TrainingConfig:
    model_name: str = Option('MODEL.NAME')
    learning_rate: float = Option('MODEL.LR', 0.001)
    epochs: int = Option('MODEL.EPOCHS', 10)
    batch_size: int = Option('MODEL.BATCH_SIZE', 32)

# Construct by passing options:
config = TrainingConfig({'MODEL': {'NAME': 'bert', 'LR': 0.0001}})
config.model_name      # => 'bert'
config.learning_rate   # => 0.0001
config.epochs          # => 10

# Use as a dataset dependency:
@dataset
def train(config: TrainingConfig = TrainingConfig) -> dict:
    return run_training(config.model_name, config.learning_rate, config.epochs)
```

## MyPy Plugin

Labrea includes a MyPy plugin for better type checking with interfaces and
datasetclasses.

```ini
# mypy.ini or pyproject.toml
[mypy]
plugins = labrea.mypy.plugin
```

This enables:
- Proper type inference for `@interface` member access
- `@datasetclass` attribute type checking
- Correct typing for `Option.namespace` members
