import typing
from types import FunctionType
from typing import Any, Dict, Optional, Tuple, Type, Union

from ._aliases import default_alias, default_aliases
from .datasets import Dataset, Overload, abstractdataset, dataset
from .options import Option
from .types import Alias, Evaluatable, MultiAlias, Value


def _is_member(key: str):
    return not key.startswith("_") and key not in ("implementation",)


class ImplementationDecorator:
    def __get__(self, instance, owner):
        def wrapper_builder(*args, **outer_kwargs):
            """Class decorator for implementing interfaces.

            Can either by used as :code:`MyInterface.implementation` or
            :code:`Interface.implementation(Interface1, Interface2)` to
            implement multiple interfaces at once.

            See :func:`interface` for example usage.
            """

            def implementation_wrapper(cls: Optional[Type] = None, **inner_kwargs):
                kwargs = {**outer_kwargs, **inner_kwargs}
                interfaces = (*args, *kwargs.pop("interfaces", tuple()))

                if cls is None:
                    return wrapper_builder(*interfaces, **kwargs)

                return Implementation(
                    cls.__name__,
                    tuple(base for base in cls.__bases__ if base is not object),
                    {
                        **cls.__dict__,
                        **{
                            "__qualname__": cls.__qualname__,
                        },
                    },
                    interfaces=interfaces,
                    **kwargs,
                )

            return implementation_wrapper

        if instance is None:
            return wrapper_builder
        else:
            return wrapper_builder(instance)


class Interface(type):
    """An Interface is a collection of datasets with related implementations.

    Interfaces are used to define a set of datasets that are related to each
    other. An interface is defined by a class that inherits from Interface
    (or is decorated with the :func:`interface` decorator). Interfaces are
    implemented using :code:`@MyInterface.implementation` or
    :code:`@Interface.implementation(Interface1, Interface2)` to implement
    multiple interfaces at once.

    A valid implementation of an interface must implement all of abstract
    datasets defined by the interface. Any datasets that are not abstract
    will be inherited from the interface if they are not implemented by the
    implementation.
    """

    _members: Dict[str, Dataset]

    def __init__(cls, name, bases, dct):
        cls._members = {}
        cls.__name__ = name

        dispatch = getattr(cls, "_dispatch", None)
        dispatch = dispatch or f"LABREA.IMPLEMENTATIONS.{default_alias(cls)}"
        if isinstance(dispatch, str):
            dispatch = Option(dispatch)
        cls._dispatch = dispatch

        for name, typ in getattr(cls, "__annotations__", {}).items():
            if hasattr(cls, name):
                continue

            @abstractdataset(dispatch=dispatch)
            def _dataset() -> typ:
                return NotImplemented  # pragma: nocover

            _dataset.__name__ = f"{cls.__qualname__}.{name}"

            setattr(cls, name, _dataset)

        for name, val in cls.__dict__.items():
            if not _is_member(name):
                continue

            typ = getattr(cls, "__annotations__", {}).get(name, Any)

            if isinstance(val, staticmethod):
                val = val.__get__(cls)

            if not isinstance(val, Evaluatable):
                val = Value(val)

            if not isinstance(val, Dataset):

                @dataset(dispatch=dispatch)
                def _dataset(dep: typ = val) -> typ:
                    return dep

                _dataset.__name__ = f"{cls.__qualname__}.{name}"

                val = _dataset
            else:
                val._overloads.option = cls._dispatch

            setattr(cls, name, val)

        super().__init__(cls.__name__, bases, dct)

    def __setattr__(cls, key: str, value: Any):
        if _is_member(key):
            cls._members[key] = value
        else:
            super().__setattr__(key, value)

    def __getattribute__(cls, key: str):
        if _is_member(key):
            try:
                return cls._members[key]
            except KeyError as e:
                raise AttributeError(*e.args) from e
        else:
            return super().__getattribute__(key)

    def __repr__(cls):
        return f"<Interface {cls.__qualname__}>"

    implementation = ImplementationDecorator()


class InterfaceFactory:
    """Factory function for creating interfaces.

    This is normally used as a decorator on a class to create an interface
    from the class.

    Parameters
    ----------
    dispatch : str | Evaluatable[str], optional
        How to dispath to the correct implementation of the interface.


    Example Usage
    -------------
    >>> from labrea import interface, abstractdataset, dataset, Option
    >>> @interface(dispatch='MY_INTERFACE.IMPLEMENTATION')
    ... class MyInterface:
    ...     @staticmethod  # Not required, but will avoid IDE warnings
    ...     @abstractdataset
    ...     def my_abstract_dataset() -> str:
    ...         return NotImplemented
    ...
    ...     @staticmethod
    ...     @dataset
    ...     def my_dataset(y: str = Option('Y')) -> str:
    ...         return y
    ...
    >>> @MyInterface.implementation
    ... class MyImplementation:
    ...     @staticmethod
    ...     def my_abstract_dataset(x: str = Option('X')) -> str:
    ...         return x
    ...
    >>> options = {
    ...     'X': 'x', 'Y': 'y',
    ...     'MY_INTERFACE': {'IMPLEMENTATION': 'MY_IMPLEMENTATION'}
    ... }
    >>> print(MyInterface.my_abstract_dataset(options))  # x
    >>> print(MyInterface.my_dataset(options))  # y

    See Also
    --------
    :class:`Interface`
    """

    _dispatch: Optional[Union[str, Evaluatable[str]]]

    def __init__(self, dispatch: Optional[Union[str, Evaluatable[str]]] = None):
        self._dispatch = dispatch

    @typing.overload
    def __call__(self, cls: Type, /) -> Interface:
        ...  # pragma: nocover

    @typing.overload
    def __call__(self, /, **kwargs: Any) -> "InterfaceFactory":
        ...  # pragma: nocover

    def __call__(
        self,
        cls: Optional[Type] = None,
        /,
        *,
        dispatch: Optional[Union[str, Evaluatable[str]]] = None,
        **kwargs,
    ) -> Union[Interface, "InterfaceFactory"]:
        factory = self

        if dispatch is not None:
            factory = factory.dispatch(dispatch)

        if cls is not None:
            return factory.wrap(cls)
        else:
            return factory

    def wrap(self, cls: Type) -> Interface:
        return Interface(
            cls.__name__,
            tuple(base for base in cls.__bases__ if base is not object),
            {
                **cls.__dict__,
                **{"__qualname__": cls.__qualname__, "_dispatch": self._dispatch},
            },
        )

    @staticmethod
    def dispatch(dispatch: Union[str, Evaluatable[str]]):
        return InterfaceFactory(dispatch=dispatch)


interface = InterfaceFactory()


class Implementation(type):
    _interfaces: Tuple[Interface, ...]

    def __new__(mcs, *args, **kwargs):
        return super().__new__(mcs, *args)

    def __init__(
        cls,
        *args,
        interfaces: Tuple[Interface, ...] = tuple(),
        alias: Optional[Alias] = None,
        aliases: Optional[MultiAlias] = None,
        **kwargs,
    ):
        if not (isinstance(interfaces, tuple) and len(interfaces)):
            raise TypeError("Implementations must implement at least one Interface.")

        cls._interfaces = interfaces

        aliases = aliases or []
        if alias is not None:
            aliases.append(alias)

        if not aliases:
            aliases = default_aliases(cls)

        for _interface in interfaces:
            for name_, member in _interface._members.items():
                overload = getattr(cls, name_, ...)
                if overload is ...:
                    if member.is_abstract:
                        raise TypeError(
                            f"Implementers of {_interface} " f"must implement {name_}"
                        )
                    else:
                        for alias in aliases:
                            member.register(alias, member.default)
                        continue

                if isinstance(overload, staticmethod):
                    overload = overload.__get__(cls, None)

                if isinstance(overload, FunctionType):
                    overload = Overload(overload)
                elif isinstance(overload, Overload):
                    pass
                elif isinstance(overload, Dataset):
                    if overload.is_abstract:
                        raise TypeError(
                            "Implementations may not contain abstract " "datasets."
                        )

                    overload = overload.default
                else:
                    if not isinstance(overload, Evaluatable):
                        overload = Value(overload)

                    def _overload(dep=overload):
                        return dep

                    overload = Overload(_overload)

                for alias in aliases:
                    member.register(alias, overload)

                setattr(cls, name_, overload)

        super().__init__(*args)
