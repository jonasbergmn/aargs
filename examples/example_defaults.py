from aargs import Aargs, arg


class AppConfig(Aargs):
    """AppConfig from cli arguments."""

    name: str = arg("--name", "-n", description="Your Name", default="Jonas")
    age: int = arg("--age", "-a", description="Your age", default=31)
    size: float = arg("--size", "-s", description="size", default=1.5)


if __name__ == "__main__":
    config = AppConfig.parse()

    print(f"Name: {config.name} (type: {type(config.name).__name__})")
    print(f"Age: {config.age} (type: {type(config.age).__name__})")
    print(f"Age: {config.size} (type: {type(config.size).__name__})")
