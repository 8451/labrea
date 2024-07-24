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
.. autofunction:: labrea.functions.map
.. autofunction:: labrea.functions.filter
.. autofunction:: labrea.functions.reduce

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
