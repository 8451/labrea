from typing import Callable, Optional

from mypy.plugin import ClassDefContext, Plugin
from mypy.plugins.common import add_attribute_to_class  # type: ignore
from mypy.types import Instance

DATACLASSES_DECORATOR_FULLNAME = "labrea.datasetclasses.datasetclass"
INTERFACE_DECORATOR_FULLNAME = "labrea.interfaces.interface"
IMPLEMENTATION_DECO_TYPE_FULLNAME = "labrea.interfaces.ImplementationDecorator"


class LabreaPlugin(Plugin):
    def get_class_decorator_hook_2(
        self, fullname: str
    ) -> Optional[Callable[[ClassDefContext], bool]]:
        """
        For datasetclasses using the datasetclass decorator, tell mypy that
        there is a .isntance attribute at the class level that returns an
        instance of the class. In reality, this just returns the class itself,
        but allows us to do this:
        @datasetclass
        class MyClass:
            x: int = Option('X')
        @dataset
        def my_dataset(
            inst: MyClass = MyClass.instance
        ) -> int:
            return inst.x
        """
        if fullname == DATACLASSES_DECORATOR_FULLNAME:
            return self.add_result_attribute_callback
        if fullname == INTERFACE_DECORATOR_FULLNAME:
            return self.add_implementation_attribute_callback

        return None

    @staticmethod
    def add_result_attribute_callback(ctx: ClassDefContext):
        add_attribute_to_class(
            api=ctx.api, cls=ctx.cls, name="result", typ=Instance(ctx.cls.info, [])
        )
        return True

    @staticmethod
    def add_implementation_attribute_callback(ctx: ClassDefContext):
        typ = ctx.api.named_type_or_none(IMPLEMENTATION_DECO_TYPE_FULLNAME)
        if typ is not None:
            add_attribute_to_class(
                api=ctx.api, cls=ctx.cls, name="implementation", typ=typ
            )
        return True


def plugin(version: str):
    # ignore version argument if the plugin works with all mypy versions.
    return LabreaPlugin
