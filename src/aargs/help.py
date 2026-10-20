from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from collections.abc import Sequence
    from dataclasses import Field

type HelpRow = tuple[str, str, str, str]


def default_flag_for_field(field_name: str) -> str:
    """Build the default CLI flag name for a dataclass field.

    Args:
        field_name: Name of the dataclass field.

    Returns:
        The inferred CLI flag name in ``--kebab-case`` format.
    """
    return f"--{field_name.replace('_', '-')}"


def field_keys(f: Field[Any]) -> tuple[str, ...]:
    """Return the CLI flag keys configured for a dataclass field.

    Falls back to ``--<field-name>`` (with underscores replaced by hyphens)
    when no explicit keys were provided via ``arg()``.

    Args:
        f: The dataclass field to inspect.

    Returns:
        A non-empty tuple of CLI flags associated with the field.
    """
    explicit_keys: tuple[str, ...] | None = f.metadata.get("keys")
    if explicit_keys:
        return explicit_keys
    return (default_flag_for_field(f.name),)


def build_help_rows(cls_fields: Sequence[Field[Any]]) -> list[HelpRow]:
    """Construct unpadded help table rows for a sequence of dataclass fields.

    Args:
        cls_fields: Dataclass fields to document.

    Returns:
        A list of 4-tuples ``(keys_col, description_col, default_col, type_col)``.
    """
    return [
        (
            f"Keys=[{','.join(field_keys(f))}]",
            f"desc={f.metadata.get('description', '')}",
            f"default={f.default}",
            f"type={f.type}",
        )
        for f in cls_fields
    ]


def format_help_table(rows: Sequence[HelpRow]) -> str:
    """Format help rows into an aligned multi-line table string.

    Args:
        rows: Sequence of 4-column help rows.

    Returns:
        Aligned table string, or an empty string if ``rows`` is empty.
    """
    if not rows:
        return ""

    w_keys = max(len(r[0]) for r in rows)
    w_desc = max(len(r[1]) for r in rows)
    w_def = max(len(r[2]) for r in rows)

    lines = [
        f"{keys_str:<{w_keys}} {desc_str:<{w_desc}} {def_str:<{w_def}} {type_str}"
        for keys_str, desc_str, def_str, type_str in rows
    ]
    return "\n".join(lines)
