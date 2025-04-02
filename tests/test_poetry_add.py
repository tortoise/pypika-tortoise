import subprocess  # nosec
import sys
from pathlib import Path

if sys.version_info >= (3, 11):
    from contextlib import chdir

else:
    import contextlib
    import os

    class chdir(contextlib.AbstractContextManager):  # Copied from source code of Python3.13
        """Non thread-safe context manager to change the current working directory."""

        def __init__(self, path) -> None:
            self.path = path
            self._old_cwd: list[str] = []

        def __enter__(self) -> None:
            self._old_cwd.append(os.getcwd())
            os.chdir(self.path)

        def __exit__(self, *excinfo) -> None:
            os.chdir(self._old_cwd.pop())


def test_added_by_poetry_v2(tmp_path: Path):
    lib = Path(__file__).parent.resolve().parent
    with chdir(tmp_path):
        package = "foo"
        subprocess.run(["poetry", "new", package])  # nosec
        with chdir(package):
            r = subprocess.run(["poetry", "add", lib])  # nosec
            assert r.returncode == 0
