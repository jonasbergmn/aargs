# aargs

Unambitious, type-safe CLI argument parser for Python built on `dataclasses` with **zero dependencies**.

## Features

- **Zero dependencies**: Built purely on the Python standard library (`dataclasses`, `typing`, `sys`).
- **Declarative & Type-Safe**: Subclass `Aargs` to automatically create a dataclass whose fields and type annotations define your CLI interface.
- **Automatic Type Conversion**: Converts incoming CLI strings using field type annotations (`str`, `int`, `float`, or custom callables).
- **Custom & Default Flags**: Specify multiple flags (e.g., `"--name", "-n"`) via `arg()`, or let `aargs` infer `--field-name` automatically.
- **Built-in Help**: Automatically handles `--help` / `-h` and prints a formatted summary table.

## Requirements

- Python `>= 3.12`

## Installation

```bash
pip install aargs
```

Or with [uv](https://docs.astral.sh/uv/):

```bash
uv add aargs
```

## Quickstart

Define your configuration by subclassing `Aargs` and using `arg()` to configure flags, descriptions, and default values:

```python
from aargs import Aargs, arg


class AppConfig(Aargs):
    """AppConfig from CLI arguments."""

    name: str = arg("--name", "-n", description="Your Name", default="Jonas")
    age: int = arg("--age", "-a", description="Your age", default=31)
    size: float = arg("--size", "-s", description="Size", default=1.5)


if __name__ == "__main__":
    config = AppConfig.parse()

    print(f"Name: {config.name} (type: {type(config.name).__name__})")
    print(f"Age: {config.age} (type: {type(config.age).__name__})")
    print(f"Size: {config.size} (type: {type(config.size).__name__})")
```

### Running from the CLI

Using default values:

```bash
$ python app.py
Name: Jonas (type: str)
Age: 31 (type: int)
Size: 1.5 (type: float)
```

Passing custom arguments:

```bash
$ python app.py --name Alice -a 28 --size 2.0
Name: Alice (type: str)
Age: 28 (type: int)
Size: 2.0 (type: float)
```

You can also pass a custom argument sequence directly to `parse()` (useful for testing):

```python
config = AppConfig.parse(["--name", "Alice", "-a", "28"])
```

### Built-in Help (`--help` / `-h`)

Passing `--help` or `-h` renders the argument overview and exits:

```text
$ python app.py --help
Keys=[--name,-n] desc=Your Name default=Jonas type=<class 'str'>
Keys=[--age,-a]  desc=Your age  default=31    type=<class 'int'>
Keys=[--size,-s] desc=Size      default=1.5   type=<class 'float'>
```

## Required Arguments & Automatic Flag Names

Fields without a `default` are treated as **required**. If you omit `arg()` or don't pass explicit flag keys, `aargs` automatically defaults the flag name to `--<field-name>` (replacing underscores with hyphens):

```python
from aargs import Aargs, arg


class JobConfig(Aargs):
    input_path: str = arg("-i", "--input-path", description="Path to input file")
    workers: int = 4  # Automatically mapped to --workers with default 4
```

If a required argument or its value is missing, or if a value cannot be converted to the target type, `Aargs.parse()` raises a descriptive `ValueError`.