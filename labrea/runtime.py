import sys

if sys.version_info < (3, 11):
    from typing_extensions import Self
else:
    from typing import Self

import threading
from typing import Callable, Dict, Generic, Mapping, Optional, Type, TypeVar, Union

from .types import Options

A = TypeVar("A", covariant=True)
R = TypeVar("R", covariant=True, bound="Request")


lock = threading.Lock()


Handler = Callable[[R], A]


class Request(Generic[A]):
    options: Options

    def run(self) -> A:
        return current_runtime().run(self)

    @classmethod
    def handle(cls, handler: Handler[Self, A]) -> Handler[Self, A]:
        handle_by_default(cls, handler)
        return handler


_DEFAULT_HANDLERS: Dict[Type[Request], Handler] = {}


class Runtime:
    handlers: Mapping[Type[Request], Handler]
    previous: Optional["Runtime"]

    def __init__(
        self, handlers: Optional[Mapping[Type[Request], Handler]] = None
    ) -> None:
        self.handlers = {**_DEFAULT_HANDLERS, **(handlers or {})}
        self.previous = None

    def handle(
        self,
        request: Union[Type[R], Mapping[Type[Request], Handler]],
        handler: Optional[Handler[R, A]] = None,
    ) -> "Runtime":
        if isinstance(request, Mapping):
            return Runtime({**self.handlers, **request})
        elif isinstance(request, type) and callable(handler):
            return Runtime({**self.handlers, request: handler})  # type: ignore

        raise TypeError(
            "Runtime.handle() requires either a request type and handler, "
            "or a mapping of request types to handlers."
        )

    def run(self, request: Request[A]) -> A:
        try:
            handler = self.handlers[type(request)]
        except KeyError as e:
            raise TypeError(
                f"No handler for request type {type(request).__qualname__}"
            ) from e

        return handler(request)

    def __enter__(self):
        with lock:
            self.previous = _RUNTIMES.get(threading.current_thread())
            _RUNTIMES[threading.current_thread()] = self
            return self

    def __exit__(self, exc_type, exc_value, traceback):
        with lock:
            _RUNTIMES[threading.current_thread()] = self.previous
            self.previous = None


_RUNTIMES: Dict[threading.Thread, Runtime] = {}


def current_runtime() -> Runtime:
    with lock:
        return _RUNTIMES.setdefault(threading.current_thread(), Runtime())


def handle(
    request: Union[Type[R], Mapping[Type[Request], Handler]],
    handler: Optional[Handler[R, A]] = None,
) -> Runtime:
    return current_runtime().handle(request, handler)


def handle_by_default(request: Type[R], handler: Handler[R, A]) -> None:
    with lock:
        _DEFAULT_HANDLERS[request] = handler


def inherit(parent: threading.Thread):
    with lock:
        _RUNTIMES[threading.current_thread()] = _RUNTIMES.get(parent, Runtime())
