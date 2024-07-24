import logging
from typing import Optional, TypeVar

from . import runtime
from .computation import Effect
from .option import Option
from .runtime import Request
from .types import Evaluatable, Options

A = TypeVar("A")


class LogRequest(Request[None]):
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
    return LogRequest(logging.CRITICAL, name, msg, options).run()


def ERROR(name: str, msg: str, options: Options) -> None:
    return LogRequest(logging.ERROR, name, msg, options).run()


def WARNING(name: str, msg: str, options: Options) -> None:
    return LogRequest(logging.WARNING, name, msg, options).run()


def INFO(name: str, msg: str, options: Options) -> None:
    return LogRequest(logging.INFO, name, msg, options).run()


def DEBUG(name: str, msg: str, options: Options) -> None:
    return LogRequest(logging.DEBUG, name, msg, options).run()


def _disabled_logging_handler(request: LogRequest) -> None:
    pass


@LogRequest.handle
def _builtin_logging_handler(request: LogRequest) -> None:
    if Option("LABREA.LOGGING.DISABLED", False)(request.options):
        return _disabled_logging_handler(request)

    logging.getLogger(request.name).log(request.level, request.msg)


def disabled() -> runtime.Runtime:
    return runtime.handle(LogRequest, _disabled_logging_handler)


class LogEffect(Effect):
    level: int
    name: str
    msg: str

    def __init__(self, level: int, name: str, msg: str):
        self.level = level
        self.name = name
        self.msg = msg

    def transform(self, value: None, options: Optional[Options] = None) -> None:
        return LogRequest(self.level, self.name, self.msg, options or {}).run()

    def validate(self, options: Options) -> None:
        pass

    def explain(self, options: Optional[Options] = None) -> set[str]:
        return set()


class Logged(Evaluatable[A]):
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
        if self.log_first:
            self._request(options).run()
            return self.evaluatable.evaluate(options)
        else:
            value = self.evaluatable.evaluate(options)
            self._request(options).run()
            return value

    def validate(self, options: Options) -> None:
        self.evaluatable.validate(options)

    def keys(self, options: Options) -> set[str]:
        return self.evaluatable.keys(options)

    def explain(self, options: Optional[Options] = None) -> set[str]:
        return self.evaluatable.explain(options)

    def __repr__(self) -> str:
        return (
            f"Logged({self.evaluatable!r}, {self.level!r}, {self.name!r}, {self.msg!r})"
        )
