# Changelog

## Unreleased (2.0.0)

- Changes to dataset
  + To overload a dataset, you now *must* provide a `dispatch=` argument to the decorator
    - Previously, a default dispatch of `Option('LABREA.IMPLEMENTATIONS.pkg.module.dataset_name')` was used
    - Similarly, a dispatch argument is required for the `@interface` decorator
  + `@my_dataset.overload` now takes `alias=` as either an alias or a list of aliases
  + `where=` argument is now renamed `defaults=` fo clarity
  + `@dataset` longer accepts an `alias=` argument
  + `callbacks=` has been renamed to `effects=`
    - Now takes functions of a single argument, or `Evaluatable` objects that return such functions
    - Can also subclass the `labrea.computation.Effect` class to define custom effects
- Changes to pipelines
  + `LabreaPipeline.step` has been removed in favor of the `pipeline_step` decorator
    - Defining pipeline steps looks the same (like a dataset with empty first arg)
  + Composing pipeline steps is now done with the `+` operator rather than the `>>` operator
    - This is because `>>` is now used as an alias for the new `.apply` method on all `Evaluatable` objects
  + Pipelines are now *evaluatable*, meaning they act like a dataset the returns a function of one variable
    - This means a pipeline can be provided as an argument to a dataset definition
  + Pipelines can now be invoked in one of two ways
    - `pipeline(options)(value)`
    - `pipeline.transform(value, options)`
      + Here options can be omitted and an empty dictionary will be used
  + Pipelines now return the plain value, rather than the special `LabreaPipelineData` object
- Changes to Caching 
  + Datasets are cached, but overloads do not have their own cache
    - This means that if you overload a dataset, it will be cached in the parent dataset's cache rather than in a separate cache
  + Caching can be globally disabled by using `with labrea.cache.disabled():`
  + The `get`, `set`, and `exists` hooks in the `Cache` ABC have changed signatures
    - This only impacts those who were writing custom cache implementations 
- `Evaluatable` is now an `ABC` rather than a `Protocol`
  + This only impacts those who are extending the labrea framework with custom types
- Implementing multiple interfaces at once is now done using the `@implements` decorator
  + `@implements(Interface1, Interface2, alias='ALIAS')` 
  

## Version 1.4.0
- Release as open source