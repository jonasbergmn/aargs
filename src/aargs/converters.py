from __future__ import annotations

from types import UnionType
from typing import TYPE_CHECKING, Any, Union, cast, get_args, get_origin

if TYPE_CHECKING:
    from collections.abc import Callable

type Converter[T] = Callable[[str], T]

_TRUE_VALUES = frozenset({"true", "1"})
_FALSE_VALUES = frozenset({"false", "0"})


def str_to_bool(value: str) -> bool:
    """Convert a CLI string representation of a boolean into a ``bool``.

    Args:
        value: The raw string token from the command line.

    Returns:
        ``True`` for ``"true"``, ``"True"``, or ``"1"``;
        ``False`` for ``"false"``, ``"False"``, or ``"0"``.

    Raises:
        ValueError: If ``value`` is not a recognized boolean string.
    """
    lowered = value.lower()
    if lowered in _TRUE_VALUES:
        return True
    if lowered in _FALSE_VALUES:
        return False
    msg = "Only true, false, True, False, 1, 0 are valid"
    raise ValueError(msg)


def unwrap_optional(annotation: object) -> object:
    """Extract the underlying non-None type from an optional union annotation.

    Args:
        annotation: A type annotation, potentially a ``UnionType`` (e.g. ``int | None``).

    Returns:
        The first non-``None`` type argument if ``annotation`` is a union,
        otherwise the original annotation unchanged.
    """
    if isinstance(annotation, UnionType) or get_origin(annotation) is Union:
        non_none = [t for t in get_args(annotation) if t is not type(None)]
        return non_none[0] if non_none else str
    return annotation


def resolve_converter(annotation: object) -> Converter[Any]:
    """Resolve a field type annotation into a callable string-to-value converter.

    Args:
        annotation: The resolved type annotation for a dataclass field.

    Returns:
        A callable that converts a CLI string argument to the target type.
    """
    target_type = unwrap_optional(annotation)
    if target_type is bool:
        return str_to_bool
    if callable(target_type):
        return cast("Converter[Any]", target_type)
    return str


def convert_value[T](raw_value: str, key: str, converter: Converter[T]) -> T:
    """Convert a raw CLI string token using the resolved field converter.

    Args:
        raw_value: The raw CLI string value to convert.
        key: The CLI flag that provided the value (used in error messages).
        converter: Callable that converts a string into the target value.

    Returns:
        The converted value.

    Raises:
        ValueError: If conversion fails with a ``ValueError``.
    """
    try:
        return converter(raw_value)
    except ValueError as err:
        type_name = getattr(converter, "__name__", str(converter))
        msg = f"Invalid value '{raw_value}' for {key}: expected {type_name}"
        raise ValueError(msg) from err
