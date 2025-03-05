from typing import Dict, Optional, Set, TypeVar, cast

from . import runtime as rt
from .types import (
    Evaluatable,
    EvaluateRequest,
    ExplainRequest,
    KeysRequest,
    MaybeEvaluatable,
    ValidateRequest,
)

A = TypeVar("A")


class _MockHandler:
    mocked: Dict[int, Evaluatable]
    runtime: rt.Runtime

    def __init__(self, mocked: Dict[int, Evaluatable], runtime: rt.Runtime):
        self.mocked = mocked
        self.runtime = runtime.handle(
            {
                EvaluateRequest: self._handle_evaluate,
                ValidateRequest: self._handle_validate,
                KeysRequest: self._handle_keys,
                ExplainRequest: self._handle_explain,
            }
        )

    def _handle_evaluate(self, request: EvaluateRequest[A]) -> A:
        return cast(rt.Runtime, self.runtime.previous).run(
            EvaluateRequest(
                self.mocked.get(id(request.evaluatable), request.evaluatable),
                request.options,
            )
        )

    def _handle_validate(self, request: ValidateRequest) -> None:
        return cast(rt.Runtime, self.runtime.previous).run(
            ValidateRequest(
                self.mocked.get(id(request.validatable), request.validatable),
                request.options,
            )
        )

    def _handle_keys(self, request: KeysRequest) -> Set[str]:
        return cast(rt.Runtime, self.runtime.previous).run(
            KeysRequest(
                self.mocked.get(id(request.cacheable), request.cacheable),
                request.options,
            )
        )

    def _handle_explain(self, request: ExplainRequest) -> Set[str]:
        return cast(rt.Runtime, self.runtime.previous).run(
            ExplainRequest(
                self.mocked.get(id(request.explainable), request.explainable),
                request.options,
            )
        )


class Mock:
    """Context manager for mocking evaluatables during testing.

    During testing, it is often useful to mock a dataset or other Evaluatable to isolate the code
    being tested. This can be accomplished with overloads, but it can be cumbersome to set up and
    tear down the overloads. The Mock context manager simplifies this process by allowing you to
    provide a value (or other evaluatable) to use in place of the original evaluatable.


    Example Usage
    -------------
    >>> import labrea
    >>>
    >>> @labrea.dataset
    >>> def foo() -> str:
    ...    return "foo"
    ...
    >>> with labrea.Mock() as mock:
    ...     mock(foo, "bar")
    ...     assert foo() == "bar"
    ...
    >>> assert foo() == "foo"
    """

    mocked: Dict[int, Evaluatable]
    _handler: Optional[_MockHandler]

    def __init__(self):
        self.mocked = {}
        self._handler = None

    def mock(self, evaluatable: Evaluatable[A], mock: MaybeEvaluatable[A]) -> None:
        """Mock an evaluatable with a different value for the duration of the context manager.

        Arguments
        ---------
        evaluatable : Evaluatable[A]
            The evaluatable to override.
        mock : MaybeEvaluatable[A]
            The value to use in place of the original evaluatable.
        """
        self.mocked[id(evaluatable)] = Evaluatable.ensure(mock)

    def __call__(self, evaluatable: Evaluatable[A], mock: MaybeEvaluatable[A]) -> None:
        """Alias for :meth:`mock`."""
        return self.mock(evaluatable, mock)

    def __enter__(self) -> "Mock":
        if self._handler is not None:
            raise RuntimeError("Mock already entered")

        self._handler = _MockHandler(self.mocked, rt.current_runtime())
        self._handler.runtime.__enter__()

        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        if self._handler is None:
            raise RuntimeError("Mock already exited")

        self._handler.runtime.__exit__(exc_type, exc_val, exc_tb)
        self._handler = None
