__PARALLEL: bool = True


def is_parallel() -> bool:
    """Return whether multithreading is enabled"""
    return __PARALLEL


def enable():
    """Enable multithreading (enabled by default).

    When multithreading is enabled, the `labrea` library will attempt to
    evaluate dataset dependencies in multiple threads. This can speed up
    evaluation of datasets that involve significant IO operations, but can
    also cause issues if the datasets are not thread-safe.
    """
    global __PARALLEL
    __PARALLEL = True


def disable():
    """Disable multithreading.

    When multithreading is disabled, the `labrea` library will evaluate dataset
    dependencies in a single thread. This is useful for debugging, or when
    datasets are not thread-safe.
    """
    global __PARALLEL
    __PARALLEL = False
