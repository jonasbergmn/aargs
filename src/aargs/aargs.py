from __future__ import annotations

import sys
from dataclasses import MISSING, dataclass, field, fields
from typing import TYPE_CHECKING, Any, Self, get_type_hints, overload

from aargs.help import build_help_rows, field_keys, format_help_table
from aargs.parser import parse_tokens

if TYPE_CHECKING:
    from collections.abc import Sequence
    from dataclasses import Field

_HELP_FLAGS = frozenset({"--help", "-h"})


@overload
def arg(*keys: str, description: str = "") -> Any: ...  # noqa: ANN401


@overload
def arg[T](*keys: str, description: str = "", default: T) -> T: ...


def arg(
    *keys: str,
    description: str = "",
    default: Any = MISSING,
) -> Any:
    """Declare CLI flag metadata and an optional default for an ``Aargs`` field.

    Wraps :func:`dataclasses.field` to store CLI flag names and help text
    in the field's metadata dictionary.

    Args:
        *keys: One or more CLI flag strings (e.g. ``"--name"``, ``"-n"``).
            If omitted, the flag defaults to ``--<field-name>`` with underscores
            replaced by hyphens.
        description: Human-readable description displayed in ``--help`` output.
        default: Default value for the field when the flag is not passed on the CLI.
            If omitted, the argument is treated as required.

    Returns:
        A :class:`dataclasses.Field` descriptor configured with CLI metadata.
    """
    metadata = {"keys": keys, "description": description}
    if default is not MISSING:
        return field(default=default, metadata=metadata)
    return field(metadata=metadata)


@dataclass
class Aargs:
    """Base class that turns any subclass into a type-safe dataclass CLI parser."""

    def __init_subclass__(cls, **kwargs: Any) -> None:  # noqa: ANN401
        """Automatically decorate every subclass with :func:`dataclasses.dataclass`."""
        super().__init_subclass__(**kwargs)
        dataclass(cls)

    @classmethod
    def help(cls, raw_args: Sequence[str]) -> bool:
        """Check whether help output was requested in the given CLI arguments.

        Args:
            raw_args: Sequence of raw CLI argument tokens.

        Returns:
            ``True`` if ``"--help"`` or ``"-h"`` is present in ``raw_args``,
            ``False`` otherwise.
        """
        return any(token in _HELP_FLAGS for token in raw_args)

    @classmethod
    def render_help(cls) -> None:
        """Print a formatted help table describing all fields on this class."""
        table = format_help_table(build_help_rows(fields(cls)))
        if table:
            print(table)  # noqa: T201

    @classmethod
    def is_required(cls, f: Field[Any]) -> bool:
        """Determine whether a dataclass field is required on the command line.

        Args:
            f: The dataclass field to inspect.

        Returns:
            ``True`` if the field defines neither a ``default`` value nor a
            ``default_factory``, ``False`` otherwise.
        """
        return f.default is MISSING and f.default_factory is MISSING

    @classmethod
    def _validate_required_fields(cls, parsed_kwargs: dict[str, Any]) -> None:
        """Ensure all required dataclass fields were provided in ``parsed_kwargs``.

        Args:
            parsed_kwargs: Dictionary of field names to parsed CLI values.

        Raises:
            ValueError: If any required field is missing from ``parsed_kwargs``.
        """
        for f in fields(cls):
            if f.name not in parsed_kwargs and cls.is_required(f):
                keys = field_keys(f)
                msg = f"Did not find required argument: {', '.join(keys)}"
                raise ValueError(msg)

    @classmethod
    def parse(cls, argv: Sequence[str] | None = None) -> Self:
        """Parse CLI arguments and return a populated instance of this class.

        Args:
            argv: Sequence of CLI argument strings to parse. Defaults to
                ``sys.argv[1:]`` when ``None``.

        Returns:
            An initialized instance of ``cls`` populated with parsed and
            type-converted values.

        Raises:
            SystemExit: If ``--help`` or ``-h`` is present in ``argv``.
            ValueError: If an unknown flag is passed, a flag is missing its value,
                a required argument is omitted, or type conversion fails.
        """
        raw_args = argv if argv is not None else sys.argv[1:]

        if cls.help(raw_args):
            cls.render_help()
            raise sys.exit(None)

        type_hints = get_type_hints(cls)
        parsed_kwargs = parse_tokens(cls, raw_args, type_hints)
        cls._validate_required_fields(parsed_kwargs)

        return cls(**parsed_kwargs)
