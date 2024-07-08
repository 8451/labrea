from types import FunctionType
from typing import (
    Any,
    Callable,
    Dict,
    Hashable,
    List,
    Protocol,
    Tuple,
    Type,
    TypeVar,
    Union,
)

from .application import FunctionApplication
from .dataset import Dataset, abstractdataset, dataset
from .option import Option
from .types import Evaluatable, Value

T = TypeVar("T", bound=Type)


def interface(dispatch: Union[Evaluatable[Hashable], str]) -> Callable[[T], "T"]:
    if isinstance(dispatch, type):
        raise TypeError(
            "@interface requires that an Evaluatable (or str representing an Option) be provided "
            "to dispatch over, but a type was provided. Did you forget to provide a dispatch? "
            '(e.g. @interface instead of @interface("DISPATCH.KEY"))?'
        )

    if isinstance(dispatch, str):
        dispatch = Option(dispatch)

    def wrapper(cls):
        return Interface(cls.__name__, cls.__bases__, dict(cls.__dict__), dispatch)

    return wrapper


def implements(
    *interfaces: "Interface", alias: Union[Hashable, List[Hashable], None] = None
) -> Callable[[T], T]:
    if alias is None:
        raise ValueError(
            "The @implements decorator requires at least one alias to be provided."
        )
    aliases = tuple(alias) if isinstance(alias, list) else (alias,)

    def wrapper(cls):
        return Implementation(
            cls.__name__, cls.__bases__, dict(cls.__dict__), interfaces, aliases
        )

    return wrapper


class Interface(type):
    _dispatch: Evaluatable[Hashable]
    _members: Dict[str, Dataset]

    def __new__(mcs, name, bases, namespace, dispatch: Evaluatable[Hashable]):
        namespace["_dispatch"] = dispatch
        return super().__new__(mcs, name, bases, namespace)

    def __init__(
        cls,
        name: str,
        bases: Tuple[type, ...],
        dct: Dict[str, Any],
        dispatch: Evaluatable[Hashable],
    ):
        super().__init__(name, bases, dct)

        for name, typ in dct.get("__annotations__", {}).items():
            if name.startswith("_") or name in dct:
                continue

            def _abstractdataset():
                pass  # pragma: no cover

            _abstractdataset.__qualname__ = f"{cls.__name__}.{name}"
            _abstractdataset.__name__ = name
            setattr(cls, name, abstractdataset(_abstractdataset, dispatch=dispatch))

        for key, val in dct.items():
            if key.startswith("_"):
                continue

            if isinstance(val, staticmethod):
                val = val.__func__
                setattr(cls, key, val)

            if isinstance(val, FunctionType):
                setattr(cls, key, dataset(val, dispatch=dispatch))
            elif isinstance(val, Dataset):
                val.set_dispatch(dispatch)
            else:

                def _dataset(v=Evaluatable.ensure(val)):
                    return v

                _dataset.__qualname__ = f"{cls.__qualname__}.{key}"
                _dataset.__name__ = key
                setattr(cls, key, dataset(_dataset, dispatch=dispatch))

    def __setattr__(self, key, value):
        if key in ("implementation",):
            raise AttributeError(f"Cannot create a member called {key} on Interface.")

        super().__setattr__(key, value)

    def implementation(cls, alias: Union[Hashable, List[Hashable]]) -> Callable[[T], T]:
        if isinstance(alias, type):
            raise TypeError(
                f"@{cls.__name__}.implementation requires that at least one alias be provided, "
                f"but a type was provided. Did you forget to provide an alias? "
                f"(e.g. @{cls.__name__}.implementation instead of "
                f'@{cls.__name__}.implementation("ALIAS"))?'
            )

        return implements(cls, alias=alias)

    def __repr__(self):
        return f"<Interface {self.__module__}.{self.__qualname__}>"


class Implementation(type):
    _interfaces: Tuple[Interface, ...]

    def __new__(
        mcs,
        name,
        bases,
        namespace,
        interfaces: Tuple[Interface, ...],
        aliases: Tuple[Hashable, ...],
    ):
        namespace["_interfaces"] = interfaces
        return super().__new__(mcs, name, bases, namespace)

    def __init__(
        cls,
        name,
        bases,
        dct,
        interfaces: Tuple[Interface, ...],
        aliases: Tuple[Hashable, ...],
    ):
        super().__init__(name, bases, dct)

        members = _get_members(interfaces)
        overloads = _build_overloads(dct, members, interfaces)

        for key, member_list in members.items():
            overload = overloads.get(key)

            for member in member_list:
                if member.is_abstract and overload is None:
                    raise TypeError(f"No implementation provided for {member}.")

            if overload is not None:
                for member in member_list:
                    for alias in aliases:
                        member.register(alias, overload)

    def __repr__(self):
        return (
            f"<Implementation {self.__module__}.{self.__qualname__} of "
            f'{", ".join(i.__qualname__ for i in self._interfaces)}>'
        )


def _get_members(interfaces: Tuple[Interface, ...]) -> Dict[str, List[Dataset]]:
    members: Dict[str, List[Dataset]] = {}

    for interface_ in interfaces:
        for name, member in interface_.__dict__.items():
            if not name.startswith("_") and isinstance(member, Dataset):
                members.setdefault(name, []).append(member)

    return members


def _build_overloads(
    dct: Dict[str, Any], members: Dict[str, List[Dataset]], interfaces
) -> Dict[str, Evaluatable]:
    overloads: Dict[str, Evaluatable] = {}

    for key, val in dct.items():
        if key.startswith("_"):
            continue

        if key not in members:
            raise TypeError(
                f"No interface in {interfaces} has a member named {key} to overload."
            )

        if isinstance(val, staticmethod):
            val = val.__func__

        overload: Evaluatable
        if isinstance(val, FunctionType):
            overload = FunctionApplication.lift(val)
        elif not isinstance(val, Evaluatable):
            overload = Value(val)
        else:
            overload = val

        overloads[key] = overload

    return overloads


class _ImplDecoProto(Protocol):
    def __call__(self, alias: Hashable, *aliases: Hashable) -> Callable[[T], T]:
        ...
