import threading

import labrea.multithreading
from labrea import dataset


@dataset.nocache
def inner():
    return threading.currentThread()


@dataset.nocache
def outer(inr=inner):
    return inr


def test_multithreading():
    assert labrea.multithreading.__PARALLEL

    assert outer({}) is not threading.currentThread()

    labrea.multithreading.disable()
    assert not labrea.multithreading.__PARALLEL

    assert outer({}) is threading.currentThread()

    labrea.multithreading.enable()
    assert labrea.multithreading.__PARALLEL
