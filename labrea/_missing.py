from enum import Enum
from typing import TypeVar, Union

T = TypeVar("T")


class Missing(Enum):
    token = 0

    def __repr__(self) -> str:
        return "MISSING"


MISSING = Missing.token


MaybeMissing = Union[Missing, T]
