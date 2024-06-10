import threading

import labrea.multithreading
from labrea import dataset


@dataset.nocache
def inner():
    return threading.current_thread()


@dataset.nocache
def outer(inr=inner):
    return inr


def test_multithreading():
    assert labrea.multithreading.__PARALLEL

    assert outer({}) is not threading.current_thread()

    labrea.multithreading.disable()
    assert not labrea.multithreading.__PARALLEL

    assert outer({}) is threading.current_thread()

    labrea.multithreading.enable()
    assert labrea.multithreading.__PARALLEL
