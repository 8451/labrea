Labrea API
==========

Core Types
----------
.. autoclass:: labrea.types.Evaluatable
   :members:
   :show-inheritance:

.. autoclass:: labrea.Value
   :members:
   :show-inheritance:

.. autoclass:: labrea.types.Apply
    :members:
    :show-inheritance:

.. autoclass:: labrea.types.Bind
    :members:
    :show-inheritance:

.. autoclass:: labrea.types.Cacheable
    :members:
    :show-inheritance:

.. autoclass:: labrea.types.Validatable
    :members:
    :show-inheritance:

.. autoclass:: labrea.types.Explainable
    :members:
    :show-inheritance:

Options
-------
.. autoclass:: labrea.Option
   :members:
   :show-inheritance:

.. autoclass:: labrea.WithOptions
   :members:
   :show-inheritance:

.. autofunction:: labrea.WithDefaultOptions

.. py:data:: labrea.AllOptions

        A special value that evaluates to the entire options dictionary.

Datasets
--------
.. autoclass:: labrea.dataset.Dataset
   :members:
   :show-inheritance:

.. autofunction:: labrea.dataset

.. autofunction:: labrea.abstractdataset

Conditionals
------------
.. autoclass:: labrea.Switch
    :members:
    :show-inheritance:

.. autoclass:: labrea.conditional.CaseWhen
    :members:
    :show-inheritance:

.. autofunction:: labrea.case

.. autoclass:: labrea.Coalesce
    :members:
    :show-inheritance:

Overloads
---------

.. autoclass:: labrea.Overloaded
    :members:
    :show-inheritance:

Interfaces
----------
.. autoclass:: labrea.interface.Interface
    :members:
    :show-inheritance:

.. autoclass:: labrea.interface.Implementation
    :members:
    :show-inheritance:

.. autofunction:: labrea.interface
.. autofunction:: labrea.implements

Iterables & Collections
-----------------------
.. autoclass:: labrea.Iter
    :members:
    :show-inheritance:


.. autofunction:: labrea.evaluatable_list
.. autofunction:: labrea.evaluatable_tuple
.. autofunction:: labrea.evaluatable_set
.. autofunction:: labrea.evaluatable_dict


.. autoclass:: labrea.Map
    :members:
    :show-inheritance:

Pipelines
---------
.. autoclass:: labrea.pipeline.PipelineStep
    :members:
    :show-inheritance:

.. autoclass:: labrea.pipeline.Pipeline
    :members:
    :show-inheritance:

.. autofunction:: labrea.pipeline_step

Pipeline Helper Functions
-------------------------

Generic
~~~~~~~
.. autofunction:: labrea.functions.partial
.. autofunction:: labrea.functions.into
.. autofunction:: labrea.functions.ensure
.. autofunction:: labrea.functions.get_attribute
.. autofunction:: labrea.functions.call_method

Collections
~~~~~~~~~~~
.. autofunction:: labrea.functions.map
.. autofunction:: labrea.functions.filter
.. autofunction:: labrea.functions.reduce
.. autofunction:: labrea.functions.flatten
.. autofunction:: labrea.functions.flatmap
.. autofunction:: labrea.functions.map_items
.. autofunction:: labrea.functions.map_keys
.. autofunction:: labrea.functions.map_values
.. autofunction:: labrea.functions.filter_items
.. autofunction:: labrea.functions.filter_keys
.. autofunction:: labrea.functions.filter_values
.. autofunction:: labrea.functions.concat
.. autofunction:: labrea.functions.append
.. autofunction:: labrea.functions.intersect
.. autofunction:: labrea.functions.union
.. autofunction:: labrea.functions.difference
.. autofunction:: labrea.functions.symmetric_difference
.. autofunction:: labrea.functions.merge
.. autofunction:: labrea.functions.get
.. autofunction:: labrea.functions.get_from
.. autofunction:: labrea.functions.length

Math
~~~~
.. autofunction:: labrea.functions.add
.. autofunction:: labrea.functions.subtract
.. autofunction:: labrea.functions.multiply
.. autofunction:: labrea.functions.left_multiply
.. autofunction:: labrea.functions.divide_by
.. autofunction:: labrea.functions.divide_into
.. autofunction:: labrea.functions.negate
.. autofunction:: labrea.functions.modulo


Predicates
~~~~~~~~~~
.. autofunction:: labrea.functions.eq
.. autofunction:: labrea.functions.ne
.. autofunction:: labrea.functions.lt
.. autofunction:: labrea.functions.le
.. autofunction:: labrea.functions.gt
.. autofunction:: labrea.functions.ge
.. autofunction:: labrea.functions.positive
.. autofunction:: labrea.functions.negative
.. autofunction:: labrea.functions.non_positive
.. autofunction:: labrea.functions.non_negative
.. autofunction:: labrea.functions.is_none
.. autofunction:: labrea.functions.is_not_none
.. autofunction:: labrea.functions.has_remainder
.. autofunction:: labrea.functions.even
.. autofunction:: labrea.functions.odd
.. autofunction:: labrea.functions.any
.. autofunction:: labrea.functions.all
.. autofunction:: labrea.functions.invert
.. autofunction:: labrea.functions.instance_of
.. autofunction:: labrea.functions.is_in
.. autofunction:: labrea.functions.is_not_in
.. autofunction:: labrea.functions.one_of
.. autofunction:: labrea.functions.none_of
.. autofunction:: labrea.functions.contains
.. autofunction:: labrea.functions.does_not_contain
.. autofunction:: labrea.functions.intersects
.. autofunction:: labrea.functions.disjoint_from



Templates
---------
.. autoclass:: labrea.Template
   :members:
   :show-inheritance:


DatasetClasses
--------------
.. autofunction:: labrea.datasetclass


Function Application
--------------------
.. autoclass:: labrea.arguments.Arguments
    :members:
    :show-inheritance:

.. autoclass:: labrea.arguments.EvaluatableArgs
    :members:
    :show-inheritance:

.. autoclass:: labrea.arguments.EvaluatableKwargs
    :members:
    :show-inheritance:

.. autoclass:: labrea.arguments.EvaluatableArguments
    :members:
    :show-inheritance:

.. autofunction:: labrea.arguments.arguments

.. autoclass:: labrea.application.FunctionApplication
    :members:
    :show-inheritance:

.. autoclass:: labrea.application.PartialApplication
    :members:
    :show-inheritance:


Runtime
-------
.. autoclass:: labrea.runtime.Request
    :members:
    :show-inheritance:

.. autoclass:: labrea.runtime.Runtime
    :members:
    :show-inheritance:

.. autofunction:: labrea.runtime.current_runtime
.. autofunction:: labrea.runtime.handle
.. autofunction:: labrea.runtime.handle_by_default
.. autofunction:: labrea.runtime.inherit


Computation
-----------
.. autoclass:: labrea.computation.Effect
    :members:
    :show-inheritance:

.. autoclass:: labrea.computation.ChainedEffect
    :members:
    :show-inheritance:

.. autoclass:: labrea.computation.CallbackEffect
    :members:
    :show-inheritance:

.. autoclass:: labrea.computation.Computation
    :members:
    :show-inheritance:


Caching
-------
.. autoclass:: labrea.cache.Cached
    :members:
    :show-inheritance:

.. autofunction:: labrea.cached

.. autoclass:: labrea.cache.Cache
    :members:
    :show-inheritance:

.. autoclass:: labrea.cache.MemoryCache
    :members:
    :show-inheritance:

.. autoclass:: labrea.cache.NoCache
    :members:
    :show-inheritance:

.. autoclass:: labrea.cache.CacheSetRequest
    :members:
    :show-inheritance:

.. autoclass:: labrea.cache.CacheGetRequest
    :members:
    :show-inheritance:

.. autoclass:: labrea.cache.CacheExistsRequest
    :members:
    :show-inheritance:


Logging
-------
.. autoclass:: labrea.logging.LogRequest
    :members:
    :show-inheritance:

.. autoclass:: labrea.logging.Logged
    :members:
    :show-inheritance:

.. autoclass:: labrea.logging.LogEffect
    :members:
    :show-inheritance:

.. autofunction:: labrea.logging.disabled
.. autofunction:: labrea.logging.DEBUG
.. autofunction:: labrea.logging.INFO
.. autofunction:: labrea.logging.WARNING
.. autofunction:: labrea.logging.ERROR
.. autofunction:: labrea.logging.CRITICAL


Exceptions
----------
.. autoclass:: labrea.exceptions.EvaluationError
    :members:
    :show-inheritance:

.. autoclass:: labrea.exceptions.KeyNotFoundError
    :members:
    :show-inheritance:

.. autoclass:: labrea.exceptions.InsufficientInformationError
    :members:
    :show-inheritance:
