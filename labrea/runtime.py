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
    """Base class for all requests.

    Requests are objects that are passed to the runtime to be handled by a
    handler. The handler is responsible for processing the request and returning
    a result. Requests are used to represent side effects using data, and allow
    the runtime to execute the side effects in a controlled manner.
    """

    options: Options

    def run(self) -> A:
        """Runs the request using the current runtime, returning the result.

        This method should not be overridden.
        """
        return current_runtime().run(self)

    @classmethod
    def handle(cls, handler: Handler[Self, A]) -> Handler[Self, A]:
        """Decorator to register a default handler for a request type.

        This method should not be overridden.

        Arguments
        ----------
        handler : Handler[Self, A]
            The handler to register for the request type.

        Returns
        -------
        Handler[Self, A]
            The handler that was registered.


        Example Usage
        -------------
        >>> class PrintRequest(Request[None]):
        ...     msg: str
        ...     def __init__(self, msg: str, options: Options) -> None:
        ...         self.msg = msg
        ...         self.options = options
        >>>
        >>> @MyRequest.handle
        ... def print_handler(request: MyRequest) -> str:
        ...     print(request.msg)
        >>>
        >>> PrintRequest("Hello, world!", {}).run()
        Hello, world!
        """
        handle_by_default(cls, handler)
        return handler


_DEFAULT_HANDLERS: Dict[Type[Request], Handler] = {}


class Runtime:
    """A class that manages the execution of requests via handlers.

    Runtimes are used to execute side effects in a controlled manner. They
    maintain a mapping of request types to handlers, and execute the appropriate
    handler for each request.

    Can be used as a context manager, which sets the current runtime for the
    duration of the context block for the current thread.

    Arguments
    ----------
    handlers : Optional[Mapping[Type[Request], Handler]]
        A mapping of request types to handlers. If provided, these handlers will
        be used in place of the default handlers.
    """

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
        """Creates a new runtime with the provided request type and handler.

        This method returns a new runtime with the provided request type and
        handler registered. The new runtime will inherit the handlers from the
        current runtime, and will override any handlers for the provided request
        type.

        Arguments
        ----------
        request : Union[Type[R], Mapping[Type[Request], Handler]]
            The request type to handle, or a mapping of request types to handlers.
        handler : Optional[Handler[R, A]]
            The handler to register for the request type.

        Returns
        -------
        Runtime
            A new runtime with the provided request type and handler registered.

        Raises
        ------
        TypeError
            If the request is not a request type or a mapping of request types to
            handlers.
        """
        if isinstance(request, Mapping):
            return Runtime({**self.handlers, **request})
        elif isinstance(request, type) and callable(handler):
            return Runtime({**self.handlers, request: handler})  # type: ignore

        raise TypeError(
            "Runtime.handle() requires either a request type and handler, "
            "or a mapping of request types to handlers."
        )

    def run(self, request: Request[A]) -> A:
        """Runs the provided request using the registered handler.

        This is not meant to be called directly. Instead, use the `run()` method
        on the request object.

        Arguments
        ----------
        request : Request[A]
            The request to run.

        Returns
        -------
        A
            The result of running the request with the correct handler.
        """

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
    """Returns the current runtime for the current thread."""
    with lock:
        return _RUNTIMES.setdefault(threading.current_thread(), Runtime())


def handle(
    request: Union[Type[R], Mapping[Type[Request], Handler]],
    handler: Optional[Handler[R, A]] = None,
) -> Runtime:
    """Alias for current_runtime().handle(request, handler).

    This is useful when using the runtime as a context manager.

    Arguments
    ----------
    request : Union[Type[R], Mapping[Type[Request], Handler]]
        The request type to handle, or a mapping of request types to handlers.
    handler : Optional[Handler[R, A]]
        The handler to register for the request type.

    Returns
    -------
    Runtime
        A new runtime with the provided request type and handler registered


    Example Usage
    -------------
    >>> with handle(MyRequest, my_handler):
    ...     MyRequest("Hello, world!", {}).run()
    """
    return current_runtime().handle(request, handler)


def handle_by_default(request: Type[R], handler: Handler[R, A]) -> None:
    """Registers a default handler for a request type.

    Arguments
    ----------
    request : Type[R]
        The request type to handle.
    handler : Handler[R, A]
        The handler to register for the request type.
    """
    with lock:
        _DEFAULT_HANDLERS[request] = handler


def inherit(parent: threading.Thread) -> None:
    """Inherit the runtime from a parent thread.

    Arguments
    ----------
    parent : threading.Thread
        The parent thread to inherit the runtime from.
    """
    with lock:
        _RUNTIMES[threading.current_thread()] = _RUNTIMES.get(parent, Runtime())
