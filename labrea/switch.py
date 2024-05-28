from typing import Dict, Set, TypeVar, Union

from .options import _UNREACHABLE, Option
from .types import (
    Evaluatable,
    EvaluationError,
    JSONDict,
    JSONType,
    ValidationError,
    Value,
)

A = TypeVar("A")


class Switch(Evaluatable[A]):
    """A switch statement that evaluates to one of several Evaluatables

    Takes an Evaluatable that evaluates to a value, and a dict of values to
    lookup. If the value is in the dict, evaluates to the corresponding
    Evaluatable. If the value is not in the dict, evaluates to the default
    Evaluatable (if provided). If no default is provided, raises an
    EvaluationError.
    """

    option: Evaluatable
    lookup: Dict[JSONType, Evaluatable[A]]
    default: Evaluatable[A]

    def __init__(
        self,
        option: Union[str, Evaluatable[JSONType]],
        lookup: Dict[JSONType, Union[Evaluatable[A], A]],
        default: Evaluatable[A] = _UNREACHABLE,
    ):
        """Create a new Switch Evaluatable

        Parameters
        ----------
        option : Union[str, Evaluatable[JSONType]]
            The Evaluatable that evaluates to the value to lookup.
            If a string is provided, it will be wrapped in an Option.
        lookup : Dict[JSONType, Union[Evaluatable[A], A]]
            The dict of values to lookup. If a value is not in the dict, the
            default will be used.
        default : Evaluatable[A]
            The default Evaluatable to use if the value is not in the dict.
            If not provided, an EvaluationError will be raised if the value is
            not in the lookup dict.
        """
        self.option = option if isinstance(option, Evaluatable) else Option(option)
        self.lookup = {
            key: val if isinstance(val, Evaluatable) else Value(val)
            for key, val in lookup.items()
        }
        self.default = default

    def get_dispatch(self, options: JSONDict) -> Evaluatable[A]:
        try:
            option_val = self.option.evaluate(options)
        except EvaluationError:
            option_val = "{NONE}"

        if not isinstance(option_val, (str, int, float, bool)):
            raise EvaluationError(
                self.option,
                option_val,
                f"{self.option} has value {option_val} of type "
                f"{type(option_val)}, but it must be of type string, int, "
                f"float, or bool.",
            )

        dispatch = self.lookup.get(option_val, self.default)

        if dispatch is _UNREACHABLE:
            raise EvaluationError(
                self.option,
                option_val,
                f"{self.option} has value {option_val}, but it "
                f"must take a value in {list(self.lookup.keys())}.",
            )

        return dispatch

    def evaluate(self, options: JSONDict) -> A:
        """Evaluate the switch statement

        Determines which entry in the lookup dict to use, and evaluates it.

        See Also
        --------
        labrea.types.Evaluatable.evaluate
        """
        dispatch = self.get_dispatch(options)
        return dispatch.evaluate(options)

    def validate(self, options: JSONDict) -> None:
        """Validate the switch statement

        Determines which entry in the lookup dict to use, and validates it.

        See Also
        --------
        labrea.types.Evaluatable.validate
        """
        try:
            dispatch = self.get_dispatch(options)
        except EvaluationError as err:
            raise ValidationError(*err.args) from err

        dispatch.validate(options)

    def keys(self, options: JSONDict) -> Set[str]:
        """Return the keys that the switch statement depends on

        Determines which entry in the lookup dict to use, and returns the keys
        that it depends on.

        See Also
        --------
        labrea.types.Evaluatable.keys
        """
        dispatch = self.get_dispatch(options)

        keys = dispatch.keys(options).copy()
        if dispatch is not self.default:
            keys.update(self.option.keys(options))

        return keys

    @property
    def has_default(self):
        return self.default is not _UNREACHABLE
