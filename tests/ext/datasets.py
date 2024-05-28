from labrea import Option
from tests.pkg.datasets import abstract, basic, dispatch


@basic.overload
def basic_overload(bsc: bool = Option("BASIC", False)) -> bool:
    return bsc


@dispatch.overload(alias="custom_alias_dispatch_overload")
def dispatch_overload() -> str:
    return "overload"


@abstract.overload
def abstract_overload() -> bool:
    return True
