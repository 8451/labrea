from labrea import Option, dataset, interface


@interface
class Interface1:
    a: int

    @staticmethod
    @dataset
    def b(bb: str = Option("B")) -> str:
        return bb

    @staticmethod
    @dataset
    def c() -> str:
        return "default"
