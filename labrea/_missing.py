from enum import Enum
from typing import TypeVar, Union

T = TypeVar("T")


class Missing(Enum):
    token = 0


MISSING = Missing.token


MaybeMissing = Union[Missing, T]
