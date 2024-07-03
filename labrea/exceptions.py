from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .types import Evaluatable


class EvaluationError(Exception):
    """Error raised when an object cannot be evaluated."""

    msg: str
    source: "Evaluatable"

    def __init__(self, msg: str, source: "Evaluatable") -> None:
        self.msg = msg
        self.source = source

        super().__init__(msg, source)

    def __str__(self):
        return f"Originating in {self.source} | {self.msg}"


class KeyNotFoundError(EvaluationError):
    """Error raised when a key is not found in the options dictionary."""

    key: str
    source: "Evaluatable"

    def __init__(self, key: str, source: "Evaluatable") -> None:
        self.key = key

        super().__init__(f"Key '{self.key}' not found", source)


class InsufficientInformationError(EvaluationError):
    """Error raised when not enough information is provided to explain an object."""

    def __init__(self, reason: str, source: "Evaluatable") -> None:
        super().__init__(
            f"Insufficient information to evaluate {source}: {reason}", source
        )
