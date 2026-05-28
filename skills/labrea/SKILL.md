---
name: labrea
description: >
  Write correct, idiomatic Python code using the labrea framework for declarative,
  functional dataset definitions. Use when writing, modifying, or understanding code
  that imports from labrea, uses @dataset decorators, Option objects,
  @interface/@implements patterns, pipeline steps, or any labrea Evaluatable types.
  Also use when working on projects that depend on the labrea package, even if the
  user does not explicitly mention "labrea".
---

# Labrea Framework

Labrea is a Python framework for writing declarative, functional code. It makes
dependencies between computations explicit and manages configuration through a
single options dictionary.

## Conceptual Model

Everything in labrea is built on **one core abstraction**: the `Evaluatable[A]`.

An `Evaluatable[A]` is a **lazy computation** that takes an options dictionary and
produces a value of type `A`. Think of it as the type `Options -> A`. Nothing runs
until `.evaluate(options)` (or equivalently, `(options)`) is called.

**Key properties of the Evaluatable monad:**

- **Lazy**: No computation happens at definition time. Evaluatables describe *what*
  to compute, not *when*.
- **Composable**: Evaluatables can depend on other Evaluatables through function
  defaults (dependency injection) or the `>>` operator (transformation chaining).
- **Cacheable**: Datasets cache results by default, keyed on the option values they
  actually read.
- **Introspectable**: Every Evaluatable can `explain()` which option keys it needs,
  `validate()` that those keys exist, and report which `keys()` it read.

### The Options Dictionary

All user configuration flows through a single `Options` dictionary:
`Mapping[str, JSON]` where `JSON = str | int | float | bool | None | Mapping | Sequence`.

Keys use **dotted notation** for nested access: `Option('A.B.C')` reads
`options['A']['B']['C']`. The options dict is always passed top-down — you never
mutate it.

### The Two Core Primitives

**`Option('KEY')`** — The simplest Evaluatable. Looks up a key in the options dict.

```python
from labrea import Option

name = Option('USER.NAME')
name({'USER': {'NAME': 'Alice'}})  # => 'Alice'

# With a default:
port = Option('PORT', 8080)
port({})  # => 8080
```

**`@dataset`** — Lifts a function into an Evaluatable. Parameters with Evaluatable
defaults are automatically resolved before the function body runs.

```python
from labrea import dataset, Option

@dataset
def greeting(name: str = Option('USER.NAME')) -> str:
    return f"Hello, {name}!"

greeting({'USER': {'NAME': 'Alice'}})  # => 'Hello, Alice!'
```

### Dependency Injection via Defaults

Datasets declare dependencies as **function parameter defaults**. When a default is
an Evaluatable (Option, another dataset, etc.), labrea resolves it from the options
dict before calling the function. Plain values remain as-is.

```python
@dataset
def radius(r: float = Option('RADIUS')) -> float:
    return r

@dataset
def area(r: float = radius) -> float:
    return 3.14159 * r ** 2

area({'RADIUS': 5})  # => 78.53975
```

The dependency graph is **implicit in the function signatures** — no separate
registration step needed.

### Caching

Datasets cache by default. The cache key is a fingerprint of the option values
the dataset actually reads. Same inputs → same cached result.

```python
@dataset
def expensive() -> list:
    return do_expensive_work()

# Second call returns cached result if options haven't changed
expensive(opts)  # computes
expensive(opts)  # cached

# Use nocache for non-deterministic functions:
@dataset.nocache
def random_id() -> str:
    return str(uuid.uuid4())
```

### Transformation Chaining (`>>`)

The `>>` operator applies a function to an Evaluatable's result, returning a new
Evaluatable. This is equivalent to `map` on the monad.

```python
import datetime as dt
start_date = Option('START_DATE') >> dt.datetime.fromisoformat
# start_date is an Evaluatable[datetime] — nothing runs yet
start_date({'START_DATE': '2024-01-01'})  # => datetime(2024, 1, 1)
```

## Core API Summary

| Symbol | Purpose |
|--------|---------|
| `Option('KEY')` | Read a value from options |
| `Option('KEY', default)` | Read with fallback |
| `Option[int]('KEY')` | Type-annotated option |
| `@dataset` | Create a cached dataset from a function |
| `@dataset.nocache` | Create an uncached dataset |
| `@dataset(dispatch='KEY')` | Dataset with overload dispatch |
| `@abstractdataset` | Dataset with no default implementation |
| `@interface('KEY')` | Group related datasets for polymorphism |
| `@implements(Iface, alias='X')` | Implement an interface |
| `@pipeline_step` | Create a composable transformation |
| `Value(x)` | Wrap a constant as an Evaluatable |
| `Switch(dispatch, lookup)` | Conditional branching |
| `Coalesce(a, b, c)` | First successful evaluation wins |
| `Template('{KEY}/path')` | String interpolation from options |

See [references/api-reference.md](references/api-reference.md) for full API details.

## Overloads and Dispatch

Datasets can have multiple implementations selected at runtime by a dispatch key:

```python
@dataset(dispatch='INPUT.SOURCE')
def load_data(path: str = Option('INPUT.PATH')) -> list:
    with open(path) as f:
        return f.readlines()

@load_data.overload('MOCK')
def mock_data() -> list:
    return ['mock', 'data']

load_data({'INPUT': {'PATH': 'data.txt'}})          # default impl
load_data({'INPUT': {'SOURCE': 'MOCK'}})             # mock overload
```

The dispatch key is an Option key. When that key is present in options, its value
selects the overload. When absent, the default implementation runs.

## Interfaces

Interfaces group related datasets that must be implemented together. They enable
swapping entire subsystems (e.g., dev vs prod data layers):

```python
from labrea import interface, implements, abstractdataset, dataset, Option

@interface('ENV')
class DataLayer:
    @abstractdataset
    def users() -> list: ...

    @dataset
    def user_count(u: list = users.__func__) -> int:
        return len(u)

@implements(DataLayer, alias='PROD')
class ProdLayer:
    @staticmethod
    @dataset
    def users(url: str = Option('DB.URL')) -> list:
        return query_db(url)

@implements(DataLayer, alias='DEV')
class DevLayer:
    @staticmethod
    @dataset
    def users() -> list:
        return [{'name': 'Test User'}]

# Use interface members like regular datasets:
DataLayer.user_count({'ENV': 'DEV'})  # => 1
```

See [references/patterns.md](references/patterns.md) for more patterns and examples.

## Gotchas

1. **Use `.__func__` when referencing a member inside its own interface**.
   Inside an `@interface` class body, methods are not yet bound. Use
   `users.__func__` (not `users`) when one member depends on another within
   the same interface definition.

2. **Use `.result` to satisfy type checkers**. Type checkers don't understand that
   Evaluatable defaults resolve to their inner type. Append `.result`:
   ```python
   @dataset
   def add(x: int = Option('X').result, y: int = Option('Y').result) -> int:
       return x + y
   ```

3. **Dispatch is required for overloads**. You must pass `dispatch=` to `@dataset`
   before calling `.overload()`. For third-party datasets, use
   `some_dataset.set_dispatch('KEY')`.

4. **Options must be JSON-serializable**. Option values must be `str | int | float |
   bool | None | list | dict`. No custom objects.

5. **Caching uses option fingerprinting**. Two calls with identical relevant option
   values return the same cached result. Use `@dataset.nocache` for
   non-deterministic computations (random values, timestamps, I/O).

6. **Avoid circular dependencies**. Labrea won't detect cycles at definition time.
   They cause infinite recursion at evaluation time.

7. **`@dataset` decorated functions are `Dataset` objects, not functions**. Don't
   call them like regular functions — call with an options dict or use as defaults
   in other datasets.

8. **Template defaults use confectioner syntax**: `Option('KEY', '{OTHER.KEY}/suffix')`
   interpolates `OTHER.KEY` from the options dict. This is different from Python
   f-strings.

9. **Pipelines use `+` not `>>`**. Compose pipeline steps with `step_a + step_b`.
   The `>>` operator is for transforming a single Evaluatable's output.

## Additional References

- [API Reference](references/api-reference.md) — Complete API with signatures, arguments, and examples
- [Common Patterns](references/patterns.md) — Idiomatic labrea patterns with full code examples
- [Advanced Features](references/advanced-features.md) — Pipelines, Templates, Effects, Runtime, helper functions
