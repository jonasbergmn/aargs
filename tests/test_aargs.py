from __future__ import annotations

import sys
from dataclasses import field, is_dataclass
from pathlib import Path

import pytest

from aargs import Aargs, arg

# ---------------------------------------------------------------------------
# Basic Dataclass & Parsing Behavior
# ---------------------------------------------------------------------------


def test_subclass_is_automatically_dataclass() -> None:
    class Config(Aargs):
        name: str = arg("--name", default="world")

    assert is_dataclass(Config)
    instance = Config()
    assert instance.name == "world"


def test_parse_defaults_with_empty_argv() -> None:
    class Config(Aargs):
        name: str = arg("--name", "-n", description="Your Name", default="Jonas")
        age: int = arg("--age", "-a", description="Your age", default=31)
        size: float = arg("--size", "-s", description="Size", default=1.5)

    config = Config.parse([])
    assert config.name == "Jonas"
    assert config.age == 31
    assert config.size == 1.5


def test_parse_long_flags() -> None:
    class Config(Aargs):
        name: str = arg("--name", "-n", default="Jonas")
        age: int = arg("--age", "-a", default=31)
        size: float = arg("--size", "-s", default=1.5)

    config = Config.parse(["--name", "Alice", "--age", "42", "--size", "2.75"])
    assert config.name == "Alice"
    assert isinstance(config.name, str)
    assert config.age == 42
    assert isinstance(config.age, int)
    assert config.size == pytest.approx(2.75)
    assert isinstance(config.size, float)


def test_parse_short_flags() -> None:
    class Config(Aargs):
        name: str = arg("--name", "-n", default="Jonas")
        age: int = arg("--age", "-a", default=31)
        size: float = arg("--size", "-s", default=1.5)

    config = Config.parse(["-n", "Bob", "-a", "25", "-s", "0.5"])
    assert config.name == "Bob"
    assert config.age == 25
    assert config.size == pytest.approx(0.5)


def test_parse_uses_sys_argv_when_argv_is_none(monkeypatch: pytest.MonkeyPatch) -> None:
    class Config(Aargs):
        host: str = arg("--host", default="localhost")
        port: int = arg("--port", "-p", default=8000)

    monkeypatch.setattr(sys, "argv", ["prog.py", "--host", "0.0.0.0", "-p", "9090"])
    config = Config.parse()
    assert config.host == "0.0.0.0"
    assert config.port == 9090


def test_parse_custom_type_converter() -> None:
    class Config(Aargs):
        path: Path = arg("--path", "-p", default=Path())

    config = Config.parse(["-p", "/tmp/example.txt"])
    assert config.path == Path("/tmp/example.txt")
    assert isinstance(config.path, Path)


def test_parse_negative_numbers_as_values() -> None:
    class Config(Aargs):
        offset: int = arg("--offset", "-o", default=0)
        delta: float = arg("--delta", "-d", default=0.0)

    config = Config.parse(["-o", "-10", "-d", "-3.14"])
    assert config.offset == -10
    assert config.delta == pytest.approx(-3.14)


# ---------------------------------------------------------------------------
# Automatic Flag Names & Required Arguments
# ---------------------------------------------------------------------------


def test_implicit_flag_name_without_arg_helper() -> None:
    class Config(Aargs):
        max_retries: int = 3
        output_dir: str = "dist"

    config = Config.parse(["--max-retries", "5", "--output-dir", "build"])
    assert config.max_retries == 5
    assert config.output_dir == "build"


def test_implicit_flag_name_with_arg_helper_and_no_keys() -> None:
    class Config(Aargs):
        batch_size: int = arg(description="Number of items per batch", default=16)

    config = Config.parse(["--batch-size", "64"])
    assert config.batch_size == 64


def test_required_argument_with_arg_helper() -> None:
    class Config(Aargs):
        input_file: str = arg("--input", "-i", description="Input path")

    config = Config.parse(["-i", "data.csv"])
    assert config.input_file == "data.csv"


def test_required_argument_without_arg_helper() -> None:
    class Config(Aargs):
        input_file: str

    config = Config.parse(["--input-file", "data.csv"])
    assert config.input_file == "data.csv"


def test_field_with_default_factory_is_not_required() -> None:
    class Config(Aargs):
        tags: str = field(default_factory=lambda: "default-tag")

    assert Config.parse([]).tags == "default-tag"


def test_inheritance_between_aargs_subclasses() -> None:
    class BaseConfig(Aargs):
        host: str = arg("--host", default="127.0.0.1")

    class ServerConfig(BaseConfig):
        port: int = arg("--port", default=8080)

    config = ServerConfig.parse(["--host", "0.0.0.0", "--port", "3000"])
    assert config.host == "0.0.0.0"
    assert config.port == 3000


# ---------------------------------------------------------------------------
# Error Handling & Validation
# ---------------------------------------------------------------------------


def test_missing_required_argument_raises_value_error() -> None:
    class Config(Aargs):
        username: str = arg("--username", "-u")

    with pytest.raises(
        ValueError, match=r"Did not find required argument: --username, -u"
    ):
        Config.parse([])


def test_missing_value_at_end_of_argv_raises_value_error() -> None:
    class Config(Aargs):
        name: str = arg("--name", "-n", default="Jonas")

    with pytest.raises(ValueError, match=r"Missing value for argument: --name"):
        Config.parse(["--name"])


def test_missing_value_before_next_flag_prevents_flag_eating() -> None:
    class Config(Aargs):
        name: str = arg("--name", "-n", default="Jonas")
        age: int = arg("--age", "-a", default=31)

    with pytest.raises(ValueError, match=r"Missing value for argument: --name"):
        Config.parse(["--name", "--age", "20"])


def test_missing_value_before_implicit_flag_prevents_flag_eating() -> None:
    class Config(Aargs):
        name: str = arg("--name", default="Jonas")
        user_age: int = 31

    with pytest.raises(ValueError, match=r"Missing value for argument: --name"):
        Config.parse(["--name", "--user-age", "20"])


def test_invalid_int_value_raises_value_error() -> None:
    class Config(Aargs):
        age: int = arg("--age", "-a", default=31)

    with pytest.raises(
        ValueError, match=r"Invalid value 'not-an-int' for --age: expected int"
    ):
        Config.parse(["--age", "not-an-int"])


def test_invalid_float_value_raises_value_error() -> None:
    class Config(Aargs):
        size: float = arg("--size", "-s", default=1.5)

    with pytest.raises(ValueError, match=r"Invalid value 'abc' for -s: expected float"):
        Config.parse(["-s", "abc"])


# ---------------------------------------------------------------------------
# Help Detection & Rendering
# ---------------------------------------------------------------------------


def test_help_detection() -> None:
    assert Aargs.help(["--help"]) is True
    assert Aargs.help(["-h"]) is True
    assert Aargs.help(["--name", "Alice", "-h"]) is True
    assert Aargs.help(["--name", "Alice"]) is False
    assert Aargs.help([]) is False


def test_parse_help_prints_table_and_exits(
    capsys: pytest.CaptureFixture[str],
) -> None:
    class Config(Aargs):
        name: str = arg("--name", "-n", description="Your Name", default="Jonas")
        age: int = arg("--age", "-a", description="Your age", default=31)

    with pytest.raises(SystemExit):
        Config.parse(["--help"])

    captured = capsys.readouterr().out
    assert "Keys=[--name,-n]" in captured
    assert "desc=Your Name" in captured
    assert "default=Jonas" in captured
    assert "Keys=[--age,-a]" in captured
    assert "desc=Your age" in captured
    assert "default=31" in captured


def test_render_help_on_empty_subclass(capsys: pytest.CaptureFixture[str]) -> None:
    class EmptyConfig(Aargs):
        pass

    EmptyConfig.render_help()
    assert capsys.readouterr().out == ""


# ---------------------------------------------------------------------------
# Edge Cases & Potential Bugs
# ---------------------------------------------------------------------------


def test_render_help_with_plain_dataclass_field_without_arg_helper(
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Fields defined without arg() work in parse(), so --help should also work."""

    class Config(Aargs):
        workers: int = 4

    with pytest.raises(SystemExit):
        Config.parse(["--help"])

    captured = capsys.readouterr().out
    assert "--workers" in captured
    assert "default=4" in captured


def test_render_help_with_arg_without_explicit_keys_shows_inferred_key(
    capsys: pytest.CaptureFixture[str],
) -> None:
    """When arg() is called without keys, render_help() should display --<field-name>."""

    class Config(Aargs):
        batch_size: int = arg(description="Batch size", default=32)

    Config.render_help()
    captured = capsys.readouterr().out
    assert "--batch-size" in captured


@pytest.mark.parametrize(
    ("raw_val", "expected"),
    [
        ("true", True),
        ("True", True),
        ("1", True),
        ("false", False),
        ("False", False),
        ("0", False),
    ],
)
def test_parse_boolean_argument_values(raw_val: str, *, expected: bool) -> None:
    """bool('false') in Python is True; CLI parser should parse false/0 as False."""

    class Config(Aargs):
        debug: bool = arg("--debug", default=False)

    config = Config.parse(["--debug", raw_val])
    assert config.debug is expected


def test_parse_optional_union_type() -> None:
    """Fields typed as `int | None` should convert non-None CLI values to `int`."""

    class Config(Aargs):
        limit: int | None = arg("--limit", default=None)

    assert Config.parse([]).limit is None
    assert Config.parse(["--limit", "10"]).limit == 10


def test_later_occurrence_of_same_flag_overrides_earlier() -> None:
    """When the same flag is passed multiple times, the last value should win."""

    class Config(Aargs):
        name: str = arg("--name", "-n", default="Jonas")

    config = Config.parse(["--name", "First", "--name", "Second"])
    assert config.name == "Second"


def test_later_alias_flag_overrides_earlier_flag() -> None:
    """When both --name and -n are passed, whichever appears later in argv should win."""

    class Config(Aargs):
        name: str = arg("--name", "-n", default="Jonas")

    config = Config.parse(["--name", "First", "-n", "Second"])
    assert config.name == "Second"


def test_unknown_arguments_raise_value_error() -> None:
    """Unrecognized CLI flags should raise a ValueError instead of being silently ignored."""

    class Config(Aargs):
        name: str = arg("--name", default="Jonas")

    with pytest.raises(ValueError):  # noqa: PT011
        Config.parse(["--unknown-flag", "value"])


def test_equals_sign_flag_syntax() -> None:
    """Flags passed as --key=value should be parsed properly."""

    class Config(Aargs):
        name: str = arg("--name", "-n", default="Jonas")
        age: int = arg("--age", "-a", default=31)

    config = Config.parse(["--name=Alice", "-a=25"])
    assert config.name == "Alice"
    assert config.age == 25
