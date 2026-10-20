from __future__ import annotations

from dataclasses import fields
from typing import TYPE_CHECKING, Any

from aargs.converters import convert_value, resolve_converter
from aargs.help import field_keys

if TYPE_CHECKING:
    from collections.abc import Mapping, Sequence
    from dataclasses import Field


def build_flag_map(cls: type[Any]) -> dict[str, Field[Any]]:
    """Map every configured or inferred CLI flag on ``cls`` to its dataclass field.

    Args:
        cls: The dataclass type to inspect.

    Returns:
        Dictionary mapping CLI flag strings (e.g. ``"--name"``, ``"-n"``)
        to their corresponding ``Field`` objects.
    """
    return {key: f for f in fields(cls) for key in field_keys(f)}


def consume_token(
    raw_args: Sequence[str],
    index: int,
    flag_to_field: Mapping[str, Field[Any]],
) -> tuple[str, str, Field[Any], int]:
    """Consume a single flag and its value from ``raw_args`` starting at ``index``.

    Supports both ``--flag value`` and ``--flag=value`` syntax.

    Args:
        raw_args: Full sequence of raw CLI argument strings.
        index: Current position in ``raw_args``.
        flag_to_field: Mapping of valid CLI flags to dataclass fields.

    Returns:
        A 4-tuple ``(flag_key, raw_value, matched_field, next_index)``.

    Raises:
        ValueError: If the flag is unknown or if a separate value token is missing.
    """
    token = raw_args[index]

    if token in flag_to_field:
        next_val_idx = index + 1
        if next_val_idx >= len(raw_args) or raw_args[next_val_idx] in flag_to_field:
            msg = f"Missing value for argument: {token}"
            raise ValueError(msg)
        return token, raw_args[next_val_idx], flag_to_field[token], index + 2

    if "=" in token:
        key, raw_val = token.split("=", 1)
        if key not in flag_to_field:
            msg = f"Unknown argument: {key}"
            raise ValueError(msg)
        return key, raw_val, flag_to_field[key], index + 1

    msg = f"Unknown argument: {token}"
    raise ValueError(msg)


def parse_tokens(
    cls: type[Any],
    raw_args: Sequence[str],
    type_hints: Mapping[str, Any],
) -> dict[str, Any]:
    """Parse sequential CLI tokens into a dictionary of field keyword arguments.

    Later occurrences of a flag or its aliases override earlier values.

    Args:
        cls: The ``Aargs`` subclass being parsed.
        raw_args: Sequence of CLI tokens.
        type_hints: Resolved type annotations for ``cls``.

    Returns:
        Dictionary mapping field names to converted argument values.

    Raises:
        ValueError: On unknown flags, missing flag values, or conversion errors.
    """
    flag_to_field = build_flag_map(cls)
    parsed_kwargs: dict[str, Any] = {}

    index = 0
    while index < len(raw_args):
        key, raw_val, matched_field, index = consume_token(
            raw_args, index, flag_to_field
        )
        converter = resolve_converter(type_hints.get(matched_field.name, str))
        parsed_kwargs[matched_field.name] = convert_value(raw_val, key, converter)

    return parsed_kwargs
