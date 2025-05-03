# Changelog

## Version 2.1.2
- Update type-hint for `@Option.namespace` to make namespaces easier to use with type checkers

## Version 2.1.1
- Fix bug introduced in 2.1.0 where exceptions raised during `.evaluate` are all masked as `EvaluationError`

## Version 2.1.0
- Add many helper functions in `labrea.functions`:
  + `partial`
    - Analog of `functools.partial`
  + `into`
    - Analog of `*` unpacking but for an evaluatable that returns an iterable
  + `ensure`
    - Make an assertion before continuing to next step
  + `get_attribute`
    - Get attribute from an object
  + `call_method`
    - Call a method on an object
  + `flatten`
    - Flatten an interable of iterables
  + `flatmap`
    - Map then flatten result
  + `map_items`, `map_keys`, and `map_values`
    - Analogs of `map` but for mapping types
  + `filter_items`, `filter_keys`, and `filter_values`
    - Analogs of `filter` but for mapping types
  + `concat`, `append`
    - Add items to an interable
  + `intersect`, `union`, `difference`, `symmetric_difference`
    - Set operations
  + `merge`
    - Merge two dictionaries
  + `get`, `get_from`
    - Get a key from an indexable object
  + `length`
  + `add`, `subtract`, `multiply`, `divide_by`, `left_multiply`, `divide_into`, `negate`, `modulo`
    - Basic math operations
  + `eg`, `ne`, `lt`, `le`, `gt`, `ge`
    - Basic comparison operations
  + `positive`, `negative`, `non_positive`, `non_negative`
    - Common comparisons
  + `is_none`, `is_not_none`
    - Check if an object is None
  + `has_remainder`, `even`, `odd`
    - Checking modulo of a number
  + `any`, `all`
    - Check if multiple predicates hold
  + `invert`
    - Invert a boolean value
  + `instance_of`
    - Check if an object is an instance of a class
  + `is_in`, `is_not_in`, `one_of`, `none_of`, `contains`, `does_not_contain`, `intersects`, `disjoint_from`
    - Check if a value is another collection
- Add optional `type` and `domain` arguments to the `Option` constructor
  + `type` is a type hint for the value of the option
    - By default, not enforced at runtime
    - An optional `labrea-type-validation` package is planned to enforce with pydantic
    - Can use `Option[Type]("KEY")` syntax instead
  + `domain` is one of
    - A container of valid values
    - A predicate function
    - An evaluatable that returns one of the above
- Add `@Option.namespace` decorator for creating option namespaces
  + Also `Option.auto` helper method for creating options within a namespace
- Add `Option.set` method for setting the value of an option in a dictionary
- Add `callback` argument to `@dataset` decorator for providing a callback function to be called after the dataset is evaluated
  - This callback is inherited by all overloads of the dataset
- Add the ability to stack the `Dataset.overload` decorator with the `@dataset` decorator
  - This allows for a nested overload tree to be defined
- Add new `TypeValidationRequest` for validating types
  - `Option`s will run this request when evaluated, but by default no handler is provided
- Add request types for the core `.evaluate`, `.validate`, `.keys`, and `.explain` methods
  - By default these just call the class' implementation
  - Can be handled to provide custom behavior, such as mocking
- Improved logging for the evaluation traceback
- Modify `PartialApplication` type to work even if multiple arguments are missing
- Allow `dataset.where` to be used with functions with `**kwargs`
- Fix a bug that cause caching to be susceptible to hash collisions.

## Version 2.0.4
- Make the `Dataset` type pickleable

## Version 2.0.3
- Fix bug introduced in 2.0.3 where dispatch is called with no options

## Version 2.0.2
- Allow `dataset` to be used to directly wrap an evaluatable
- Fix bug in `Switch.keys` that didn't properly handle when the dispatch by default will evaluate to something

## Version 2.0.1
- Fix bug where pipeline steps are evaluated before their inputs

## Version 2.0.0
### Breaking Changes
- Module structure has been fully changed.
  + Any imports that look like `from labrea.<module> import <object>` will need to be updated
- Changes to dataset
  + To overload a dataset, you now *must* provide a `dispatch=` argument to the decorator
    - Previously, a default dispatch of `Option('LABREA.IMPLEMENTATIONS.pkg.module.dataset_name')` was used
    - Similarly, a dispatch argument is required for the `@interface` decorator
  + `@my_dataset.overload` now takes `alias=` as either an alias or a list of aliases
    - Previously, `aliases=` was used for a list of aliases
  + `where=` argument is now renamed `defaults=` for clarity
  + `@dataset` no longer accepts an `alias=` argument
  + `callbacks=` has been renamed to `effects=`
    - Now takes functions of a single argument, or `Evaluatable` objects that return such functions
    - Can also subclass the `labrea.computation.Effect` class to define custom effects
- Changes to options
  + Previously, it was implicitly assumed that options must be a JSON-serializable dictionary
  + This is now enforced. Providing a non-serializable option will raise an error
    - e.g. a Pandas DataFrame cannot be provided as an option value
- Changes to pipelines
  + `LabreaPipeline.step` has been removed in favor of the `pipeline_step` decorator
    - Defining pipeline steps looks the same (like a dataset with empty first arg)
  + Composing pipeline steps is now done with the `+` operator rather than the `>>` operator
    - This is because `>>` is now used as an alias for the new `.apply` method on all `Evaluatable` objects
  + Pipelines can now be invoked in one of two ways
    - `pipeline(options)(value)`
    - `pipeline.transform(value, options)`
      + Here options can be omitted and an empty dictionary will be used
  + Pipelines now return the plain value, rather than the special `LabreaPipelineData` object
- Changes to Caching
  + Datasets are cached, but overloads do not have their own cache
    - This means that if you overload a dataset, it will be cached in the parent dataset's cache rather than in a separate cache
  + The `get`, `set`, and `exists` hooks in the `Cache` ABC have changed signatures
    - This only impacts those who were writing custom cache implementations
- `Evaluatable` is now an `ABC` rather than a `Protocol`
  + This only impacts those who are extending the labrea framework with custom types
- Implementing multiple interfaces at once is now done using the `@implements` decorator
  + Previously done with `@Interface.implementation(Interface1, Interface2, alias='ALIAS')`
  + `@implements(Interface1, Interface2, alias='ALIAS')`

### New Features
- All `Evaluatable` objects (`datasets`, `Options`, etc.) now have a `.explain()` method that returns a set of option keys that are required to evaluate the object
  - `Option('A').explain() == {'A'}`
  - Datasets will return every option key that is required to evaluate the dataset
- All `Evaluatable` objects can be called with no argument and an empty options dictionary will be inferred
- All `Evaluatable` objects now support the following methods for chaining transformations
  + `apply` (aliased as `>>`)
    + Used to apply a function to the result of an object
    + e.g. `my_dataset >> (lambda x: x + 1)`
  + `bind`
    + Used to apply a function to the result of an object and return a new labrea object based on the result
    + e.g. `my_dataset.bind(lambda x: my_dataset2 if x > 0 else my_dataset3)`
- Utility functions for some common operations for chaning together
  + `labrea.functions.map` recreates the `map` function for labrea objects
    + `my_list_dataset >> labrea.functions.map(lambda x: x + 1)`
  + `labrea.functions.filter` recreates the `filter` function for labrea objects
    + `my_list_dataset >> labrea.functions.filter(lambda x: x > 0)`
  + `labrea.functions.reduce` recreates the `reduce` function for labrea objects
    + `my_list_dataset >> labrea.functions.reduce(lambda x, y: x + y)`
- New `@pipeline_step` decorator for defining pipeline steps
  + Pipelines are now *evaluatable*, meaning they act like a dataset the returns a function of one variable
    - This means a pipeline can be provided as an argument to a dataset definition
- New case / when / otherwise syntax for defining conditional logic that can't be expressed with switches/overloads
  + `case(Option('A')).when(lambda a: a > 0, positive_dataset).otherwise(negative_dataset)`
- New `Map` type for mapping a dataset over multiple options values
  + `Map(Option('A'), {'A': [1, 2, 3]}).apply(list)()` == `[1, 2, 3]`
- New `WithOptions` type that can be used to provide pre-set options to an `Evaluatable` object
  + `my_dataset_a_1 = WithOptions(my_dataset, {'A': 1})`
- New `@implements` decorator for implementing multiple interfaces at once
  + `@implements(Interface1, Interface2, alias='ALIAS')`
- New `Cached` type that can cache any labrea object (not just datasets)
- New `Overloaded` type that can provide overloads for any labrea object (not just datasets)
- New `FunctionApplication`, `PartialApplication`, and `EvaluatableArguments` types that are the foundational building blocks for datasets and pipeline steps
- New effects system and corresponding `Computation` type that performs side-effects after an evaluation of a labrea object
- New `runtime` module used for handling managed effects

## Version 1.4.0
- Release as open source
