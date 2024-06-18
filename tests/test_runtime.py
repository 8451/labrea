import pytest
import threading
from labrea.runtime import Request, handle, inherit


class UnhandledRequest(Request):
    def __init__(self, value):
        self.value = value


class EchoRequest(Request[str]):
    message: str

    def __init__(self, message: str):
        self.message = message


@EchoRequest.handle
def echo(request: EchoRequest) -> str:
    return request.message


def void(request) -> None:
    pass


def test_request():
    assert EchoRequest("hello").run() == "hello"

    with pytest.raises(TypeError):
        UnhandledRequest("world").run()


def test_handle():
    assert EchoRequest("hello").run() == "hello"

    with handle(EchoRequest, void):
        assert EchoRequest("hello").run() is None

    with handle(EchoRequest, void):
        with handle(EchoRequest, echo):
            assert EchoRequest("hello").run() is "hello"

    with handle({EchoRequest: void}):
        assert EchoRequest("hello").run() is None

    with handle({EchoRequest: void, UnhandledRequest: void}):
        assert EchoRequest("hello").run() is None
        assert UnhandledRequest("world").run() is None

    assert EchoRequest("hello").run() == "hello"

    with pytest.raises(TypeError):
        with handle(42, void):
            pass

    with pytest.raises(TypeError):
        with handle(EchoRequest, 42):
            pass


def test_inherit():
    def worker(parent: threading.Thread, request: Request):
        inherit(parent)
        return request.run()

    with pytest.raises(TypeError):
        threading.Thread(target=worker, args=(threading.current_thread(), UnhandledRequest("hello"))).run()

    with handle(UnhandledRequest, void):
        threading.Thread(target=worker, args=(threading.current_thread(), UnhandledRequest("hello"))).run()
