import typing
from collections import OrderedDict
from typing import Generic, Optional, TypeVar

from .types import Callback, Evaluatable, JSONDict

A = TypeVar("A", covariant=True)


PreCallback = Callback[Evaluatable[A], JSONDict]
PostCallback = Callback[A, A]


class EarlyExit(Generic[A], Exception):
    """An exception to signal that the evaluation should stop early."""

    value: A

    def __init__(self, value: A, *args):
        self.value = value
        super().__init__(*args)


class Callbacks(Generic[A]):
    """A collection of callbacks to be applied to an Evaluatable.

    Callbacks are functions that take an Evaluatable and an options dictionary
    and return a value. They are used to extend the behavior of an Evaluatable
    by running a computation before or after the .evaluate() method is called.

    Parameters
    ----------
    pre : typing.OrderedDict[PreCallback]
        A list of callbacks to run before the .evaluate() method is called.
        Takes an Evaluatable and an options dictionary and optionally returns
        a new Evaluatable and options dictionary.
    post : typing.OrderedDict[PostCallback]
        A list of callbacks to run after the .evaluate() method is called.
        Takes the result of the .evaluate() method and an options dictionary
        and optionally returns a new result.
    """

    pre: typing.OrderedDict[str, PreCallback[A]]
    post: typing.OrderedDict[str, PostCallback[A]]

    def __init__(
        self,
        pre: Optional[typing.OrderedDict[str, PreCallback[A]]] = None,
        post: Optional[typing.OrderedDict[str, PostCallback[A]]] = None,
    ):
        self.pre = pre or OrderedDict()
        self.post = post or OrderedDict()

    def __repr__(self):
        return f"{self.__class__.__name__}(pre={self.pre}, post={self.post})"
