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
