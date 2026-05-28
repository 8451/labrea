# Labrea API Reference

## Core Types

### `Options`

```python
from labrea.types import Options, JSON

Options = Mapping[str, JSON]
JSON = Union[str, int, float, bool, None, Mapping[str, JSON], Sequence[JSON]]
```

The options dictionary is the single configuration object passed through the entire
evaluation graph. Keys use dotted notation for nested access.

### `Evaluatable[A]`

Abstract base class for all lazy computations. Every labrea type inherits from this.

```python
from labrea.types import Evaluatable

class Evaluatable(Generic[A], ABC):
    def evaluate(self, options: Options) -> A: ...
    def __call__(self, options: Optional[Options] = None) -> A: ...
    def validate(self, options: Options) -> None: ...
    def keys(self, options: Options) -> Set[str]: ...
    def explain(self, options: Optional[Options] = None) -> Set[str]: ...
    def apply(self, func) -> Evaluatable[B]: ...   # also: >> operator
    def bind(self, func) -> Evaluatable[B]: ...
    @property
    def result(self) -> A: ...   # type-checker helper, returns self
    @staticmethod
    def unit(value) -> Value: ...
    @staticmethod
    def ensure(value) -> Evaluatable: ...
```

**Key methods:**
- `evaluate(options)` / `__call__(options)` — Run the computation
- `validate(options)` — Check all required keys exist (raises `KeyNotFoundError`)
- `keys(options)` — Return the set of option keys actually read
- `explain(options=None)` — Return all keys this evaluatable *could* need
- `apply(func)` / `>> func` — Transform the result lazily (returns new Evaluatable)
- `bind(func)` — Like apply, but `func` returns an Evaluatable (monadic bind)
- `.result` — Identity property that tells type checkers the value type

### `Value[A]`

Wraps a plain Python value as an Evaluatable. Ignores options entirely.

```python
from labrea import Value

v = Value(42)
v({})  # => 42
v({'anything': 'ignored'})  # => 42
```

## Option

```python
from labrea import Option
```

### Constructor

```python
Option(
    key: str,                           # Dotted key path (e.g., 'A.B.C')
    default: MaybeEvaluatable = MISSING,  # Fallback value or Evaluatable
    default_factory: Callable = MISSING,  # Factory for mutable defaults
    type: Type = Any,                   # Expected type (for validation)
    domain: Container | Callable = MISSING,  # Valid values constraint
    doc: str = "",                      # Documentation string
)
```

### Type-annotated options

```python
port = Option[int]('PORT', 8080)       # Type hint for IDE support
```

### Template defaults

```python
# Confectioner template syntax — interpolates from the options dict
log_path = Option('LOG.PATH', '{LOG.DIR}/{APP.NAME}.log')
```

### Domain validation

```python
# Container domain — value must be in the set
env = Option('ENV', domain=['dev', 'staging', 'prod'])

# Predicate domain — function must return True
count = Option('COUNT', domain=lambda x: x > 0)
```

### `Option.set(options, value) -> Options`

Returns a new options dict with this option's key set to the given value.

```python
opt = Option('A.X')
opt.set({'A': {'Y': 1}}, 'hello')  # => {'A': {'Y': 1, 'X': 'hello'}}
```

### `Option.namespace`

Decorator that creates a structured group of options from a class definition.

```python
@Option.namespace
class MY_APP:
    class DATABASE:
        HOST: str                        # Option('MY_APP.DATABASE.HOST')
        PORT: int = 5432                 # Option('MY_APP.DATABASE.PORT', 5432)
    LOG_LEVEL: str = 'INFO'              # Option('MY_APP.LOG_LEVEL', 'INFO')

MY_APP.DATABASE.PORT({})                 # => 5432
MY_APP.DATABASE.HOST({'MY_APP': {'DATABASE': {'HOST': 'localhost'}}})  # => 'localhost'
```

Custom namespace names via decorator argument:
```python
@Option.namespace
class CONFIG:
    @Option.namespace("my-custom-name")
    class SECTION:
        VALUE: str   # Option('CONFIG.my-custom-name.VALUE')
```

### `Option.auto`

Create options within namespaces that support docstrings and transformations:

```python
@Option.namespace
class CONFIG:
    PORT = Option.auto(default='8080', doc='Server port') >> int
    # Key inferred as CONFIG.PORT, value transformed to int
```

### `AllOptions`

Evaluatable that returns the entire options dictionary.

```python
from labrea import AllOptions
AllOptions({'A': 1, 'B': 2})  # => {'A': 1, 'B': 2}
```

### `WithOptions` / `WithDefaultOptions`

```python
from labrea import WithOptions, WithDefaultOptions

# Force specific options (cannot be overridden by caller):
configured = WithOptions(my_dataset, {'KEY': 'forced'})

# Provide defaults (caller can override):
defaulted = WithDefaultOptions(my_dataset, {'KEY': 'fallback'})
```

## Dataset

```python
from labrea import dataset, abstractdataset
```

### `@dataset`

Creates a cached `Dataset[A]` from a function. Parameters with Evaluatable defaults
are resolved from the options dict before the function body runs.

```python
@dataset
def add(x: int = Option('X'), y: int = Option('Y')) -> int:
    return x + y

add({'X': 1, 'Y': 2})  # => 3
```

### `@dataset(dispatch='KEY')`

Creates a dataset with overload dispatch. When `KEY` exists in options, its value
selects which overload runs.

```python
@dataset(dispatch='MODE')
def process(data: str = Option('DATA')) -> str:
    return data.upper()

@process.overload('REVERSE')
def process_reverse(data: str = Option('DATA')) -> str:
    return data[::-1]

process({'DATA': 'hello'})                  # => 'HELLO'
process({'DATA': 'hello', 'MODE': 'REVERSE'})  # => 'olleh'
```

### `@dataset.nocache`

Creates an uncached dataset. Use for non-deterministic computations.

```python
@dataset.nocache
def timestamp() -> float:
    return time.time()
```

### `@abstractdataset`

Creates a dataset with no default implementation. Must be overloaded.

```python
@abstractdataset
def load_data() -> list: ...
# Calling load_data without registering an overload raises an error
```

### `@dataset(effects=[...])`

Attach side effects that run after evaluation.

```python
results = []

@dataset(effects=[lambda x: results.append(x)])
def tracked(x: int = Option('X')) -> int:
    return x * 2
```

### `@dataset(defaults={...})`

Override parameter defaults without modifying the function.

```python
@dataset(defaults={'x': Option('CUSTOM_X')})
def compute(x: int = Option('X')) -> int:
    return x ** 2
```

### Dataset Methods

```python
ds = my_dataset

# Overloading
ds.overload('ALIAS')(func)      # Register overload by alias
ds.register('ALIAS', evaluatable)  # Register pre-built Evaluatable
ds.set_dispatch('KEY')          # Set dispatch key (for third-party datasets)

# Configuration
ds.set_cache(MemoryCache())     # Replace cache strategy
ds.add_effects(effect)          # Add side effects
ds.disable_effects()            # Turn off effects
ds.enable_effects()             # Turn on effects

# Creating variants
ds.with_options({'K': 'v'})     # New dataset with forced options
ds.with_default_options({'K': 'v'})  # New dataset with default options

# Properties
ds.is_abstract                  # True if no default implementation
ds.default                      # The default Evaluatable (or MISSING)
```

## Interface and Implements

```python
from labrea import interface, implements, abstractdataset, dataset, Option
```

### `@interface(dispatch)`

Creates a polymorphic group of related datasets. The dispatch determines which
implementation to use at runtime.

```python
@interface('BACKEND')
class Storage:
    @abstractdataset
    def save(data: dict) -> bool: ...

    @abstractdataset
    def load(key: str) -> dict: ...

    @dataset
    def save_and_confirm(
        data: dict = Option('DATA'),
        saved: bool = save.__func__
    ) -> str:
        return 'OK' if saved else 'FAIL'
```

**Interface member types:**
- `@abstractdataset` — Must be implemented by every implementation
- `@dataset` — Has a default; can be overridden
- `@staticmethod` decorated function — Auto-converted to dataset
- Type annotation (e.g., `x: int`) — Becomes an abstract dataset
- Evaluatable default (e.g., `x: int = Option('X')`) — Becomes a dataset

### `@implements(*interfaces, alias='ALIAS')`

Register an implementation for one or more interfaces.

```python
@implements(Storage, alias='LOCAL')
class LocalStorage:
    @staticmethod
    @dataset
    def save(data: dict = Option('DATA')) -> bool:
        Path('store.json').write_text(json.dumps(data))
        return True

    @staticmethod
    @dataset
    def load(key: str = Option('KEY')) -> dict:
        return json.loads(Path('store.json').read_text())
```

**Rules for implementation classes:**
- Methods must be `@staticmethod` decorated with `@dataset`
- Method names must match the interface member names
- Only abstract members *must* be implemented; default members *may* be overridden

## Conditional Evaluation

### `Switch` / `switch`

```python
from labrea import switch, Option

result = switch(
    Option('MODE'),
    {
        'A': Option('VAL_A'),
        'B': Option('VAL_B'),
    },
    default=Value('fallback')  # optional
)

result({'MODE': 'A', 'VAL_A': 42})  # => 42
```

### `Coalesce` / `coalesce`

Try evaluatables in order, return the first that succeeds.

```python
from labrea import coalesce, Option

value = coalesce(Option('PRIMARY'), Option('SECONDARY'), Value('default'))
value({'SECONDARY': 'found'})  # => 'found'
```

### `case` / `CaseWhen`

Pattern-matching style conditionals.

```python
from labrea import case, Option

result = (
    case(Option('X'))
    .when(lambda x: x > 0, Value('positive'))
    .when(lambda x: x < 0, Value('negative'))
    .otherwise(Value('zero'))
)
```

## Collections

```python
from labrea import evaluatable_list, evaluatable_dict, evaluatable_set, evaluatable_tuple
```

Build collections of evaluatables that resolve together:

```python
coords = evaluatable_list(Option('X'), Option('Y'), Option('Z'))
coords({'X': 1, 'Y': 2, 'Z': 3})  # => [1, 2, 3]

config = evaluatable_dict(host=Option('HOST'), port=Option('PORT'))
config({'HOST': 'localhost', 'PORT': 8080})  # => {'host': 'localhost', 'port': 8080}
```

## Map and Iter

### `Map`

Apply a dataset across multiple option sets:

```python
from labrea import Map, Option, dataset

@dataset
def process(x: int = Option('X')) -> int:
    return x * 2

mapped = Map(process, Option('ITEMS'))
# ITEMS should be a list of option dicts
result = mapped({'ITEMS': [{'X': 1}, {'X': 2}, {'X': 3}]})
# result.values => [2, 4, 6]
```

### `Iter`

Lazy iteration over evaluatables:

```python
from labrea import Iter, Option
items = Iter(Option('A'), Option('B'))
list(items({'A': 1, 'B': 2}))  # => [1, 2]
```

## Template

```python
from labrea import Template

t = Template('{APP.NAME} v{APP.VERSION}')
t({'APP': {'NAME': 'MyApp', 'VERSION': '1.0'}})  # => 'MyApp v1.0'

# With parameters:
t = Template('{BASE_URL}/{:endpoint:}', endpoint='users')
t({'BASE_URL': 'https://api.example.com'})  # => 'https://api.example.com/users'
```

## Errors

```python
from labrea.exceptions import EvaluationError, KeyNotFoundError, InsufficientInformationError
```

- `KeyNotFoundError` — Required option key missing from options dict
- `EvaluationError` — General evaluation failure
- `InsufficientInformationError` — Cannot determine required keys (e.g., in `explain()`)
