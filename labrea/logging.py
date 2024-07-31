import logging
from typing import Optional, Set, TypeVar

from . import runtime
from .computation import Effect
from .option import Option
from .runtime import Request
from .types import Evaluatable, Options

A = TypeVar("A")


class LogRequest(Request[None]):
    """A request to log a message.

    Arguments
    ---------
    level : int
        The logging level (see the :mod:`logging` module).
    name : str
        The name of the logger; usually the module name.
    msg : str
        The message to log.
    options : Options
        The options used during evaluation
    """

    level: int
    name: str
    msg: str
    options: Options

    def __init__(self, level: int, name: str, msg: str, options: Options):
        self.options = options
        self.level = level
        self.name = name
        self.msg = msg


def CRITICAL(name: str, msg: str, options: Options) -> None:
    """Log a message at the CRITICAL level."""
    return LogRequest(logging.CRITICAL, name, msg, options).run()


def ERROR(name: str, msg: str, options: Options) -> None:
    """Log a message at the ERROR level."""
    return LogRequest(logging.ERROR, name, msg, options).run()


def WARNING(name: str, msg: str, options: Options) -> None:
    """Log a message at the WARNING level."""
    return LogRequest(logging.WARNING, name, msg, options).run()


def INFO(name: str, msg: str, options: Options) -> None:
    """Log a message at the INFO level."""
    return LogRequest(logging.INFO, name, msg, options).run()


def DEBUG(name: str, msg: str, options: Options) -> None:
    """Log a message at the DEBUG level."""
    return LogRequest(logging.DEBUG, name, msg, options).run()


def _disabled_logging_handler(request: LogRequest) -> None:
    pass


@LogRequest.handle
def _builtin_logging_handler(request: LogRequest) -> None:
    if Option("LABREA.LOGGING.DISABLED", False)(request.options):
        return _disabled_logging_handler(request)

    logging.getLogger(request.name).log(request.level, request.msg)


def disabled() -> runtime.Runtime:
    """Return a runtime that disables logging.

    Can be used as a context manager to disable logging for the duration of the context block.


    Example Usage
    -------------
    >>> import labrea.logging
    >>> with labrea.logging.disabled():
    ...     pass
    """
    return runtime.handle(LogRequest, _disabled_logging_handler)


class LogEffect(Effect):
    """An effect that logs a message.

    Arguments
    ---------
    level : int
        The logging level (see the :mod:`logging` module).
    name : str
        The name of the logger; usually the module name.
    msg : str
        The message to log.
    """

    level: int
    name: str
    msg: str

    def __init__(self, level: int, name: str, msg: str):
        self.level = level
        self.name = name
        self.msg = msg

    def transform(self, value: None, options: Optional[Options] = None) -> None:
        """Log the message."""
        return LogRequest(self.level, self.name, self.msg, options or {}).run()

    def validate(self, options: Options) -> None:
        """Always validates"""
        pass

    def explain(self, options: Optional[Options] = None) -> Set[str]:
        """Return an empty set, as no options are required."""
        return set()


class Logged(Evaluatable[A]):
    """An Evaluatable that logs a message before (or after) evaluating another Evaluatable.

    Arguments
    ---------
    evaluatable : Evaluatable[A]
        The Evaluatable to evaluate.
    level : int
        The logging level (see the :mod:`logging` module).
    name : str
        The name of the logger; usually the module name.
    msg : str
        The message to log.
    log_first : bool, optional
        Whether to log the message before or after evaluating the Evaluatable. Default is True.
    """

    evaluatable: Evaluatable[A]
    level: int
    name: str
    msg: str
    log_first: bool

    def __init__(
        self,
        evaluatable: Evaluatable[A],
        level: int,
        name: str,
        msg: str,
        log_first: bool = True,
    ):
        self.evaluatable = evaluatable
        self.level = level
        self.name = name
        self.msg = msg
        self.log_first = log_first

    def _request(self, options: Options) -> LogRequest:
        return LogRequest(self.level, self.name, self.msg, options)

    def evaluate(self, options: Options) -> A:
        """Evaluate the Evaluatable and log the message."""
        if self.log_first:
            self._request(options).run()
            return self.evaluatable.evaluate(options)
        else:
            value = self.evaluatable.evaluate(options)
            self._request(options).run()
            return value

    def validate(self, options: Options) -> None:
        """Validate the Evaluatable."""
        self.evaluatable.validate(options)

    def keys(self, options: Options) -> Set[str]:
        """Return the option keys required to evaluate the Evaluatable."""
        return self.evaluatable.keys(options)

    def explain(self, options: Optional[Options] = None) -> Set[str]:
        """Return the option keys required to evaluate the Evaluatable."""
        return self.evaluatable.explain(options)

    def __repr__(self) -> str:
        return (
            f"Logged({self.evaluatable!r}, {self.level!r}, "
            f"{self.name!r}, {self.msg!r})"
            if self.log_first
            else f"Logged({self.evaluatable!r}, {self.level!r}, "
            f"{self.name!r}, {self.msg!r}, log_first=False)"
        )
