from labrea import dataset
from tests.pkg.interfaces import Interface1


@Interface1.implementation
class Int1Imp:
    @staticmethod
    def a() -> int:
        return 1

    @staticmethod
    @dataset
    def c() -> str:
        return "overload"
