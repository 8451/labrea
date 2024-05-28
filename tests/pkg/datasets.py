from labrea import Option, abstractdataset, dataset


@dataset
def basic(bsc: bool = Option("BASIC", True)) -> bool:
    return bsc


@dataset(dispatch="CUSTOM_DISPATCH")
def dispatch() -> str:
    return "default"


@abstractdataset
def abstract():
    ...
