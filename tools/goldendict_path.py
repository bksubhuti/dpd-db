
from pathlib import Path
from rich import print
from rich.prompt import Prompt


from tools.configger import (
    config_test_option,
    config_update,
    config_read)


def goldedict_path() -> Path:
    """Add a Goldendict path if one doesn't exist,
    or return the path if it does."""

    if not config_test_option("goldendict", "path"):
        goldendict_path = Prompt.ask(f"[yellow]Enter your GoldenDict directory (or ENTER for None)")
        config_update("goldendict", "path", goldendict_path)
        return Path(goldendict_path)
    else:
        return Path(config_read("goldendict", "path"))


if __name__ == "__main__":
    print(Path(goldedict_path()))