from typing import Callable, Optional

from mypy.plugin import ClassDefContext, Plugin
from mypy.plugins.common import Instance, add_attribute_to_class  # type: ignore

DATASETCLASS_DECORATOR_FULLNAME = "labrea.datasetclass.datasetclass"
INTERFACE_DECORATOR_FULLNAME = "labrea.interface.interface"
IMPLEMENTATION_DECO_TYPE_FULLNAME = "labrea.interface._ImplDecoProto"
EVALUATABLE_TYPE_FULLNAME = "labrea.evaluatable.Evaluatable"


class LabreaPlugin(Plugin):
    def get_class_decorator_hook_2(
        self, fullname: str
    ) -> Optional[Callable[[ClassDefContext], bool]]:
        if fullname == INTERFACE_DECORATOR_FULLNAME:
            return self.interface_callback
        if fullname == DATASETCLASS_DECORATOR_FULLNAME:
            return self.datasetclass_callback

        return None

    @staticmethod
    def interface_callback(ctx: ClassDefContext):
        for name, attribute in ctx.cls.info.names.copy().items():
            if name.startswith("_"):
                continue
            add_attribute_to_class(  # type: ignore [call-arg]
                api=ctx.api,
                cls=ctx.cls,
                name=name,
                typ=ctx.api.named_type_or_none(  # type: ignore [arg-type]
                    EVALUATABLE_TYPE_FULLNAME
                ),
                overwrite_existing=True,
            )

        add_attribute_to_class(
            api=ctx.api,
            cls=ctx.cls,
            name="implementation",
            typ=ctx.api.named_type_or_none(  # type: ignore [arg-type]
                IMPLEMENTATION_DECO_TYPE_FULLNAME
            ),
        )

        return True

    @staticmethod
    def datasetclass_callback(ctx: ClassDefContext):
        add_attribute_to_class(
            api=ctx.api, cls=ctx.cls, name="result", typ=Instance(ctx.cls.info, [])
        )
        return True


def plugin(version: str):
    # ignore version argument if the plugin works with all mypy versions.
    return LabreaPlugin
