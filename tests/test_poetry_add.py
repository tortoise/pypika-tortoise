import shlex
import shutil
import subprocess  # nosec
import sys
from pathlib import Path

import pytest


def _run_shell(cmd: str) -> int:
    return subprocess.call(shlex.split(cmd))  # nosec


def test_added_by_poetry_v2(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    lib = Path(__file__).parent.resolve().parent
    py = "{}.{}".format(*sys.version_info)
    poetry = "poetry"
    if shutil.which(poetry) is None:
        poetry = "uvx " + poetry

    monkeypatch.chdir(tmp_path)
    package = "foo"
    _run_shell(f"{poetry} new {package} --python=^{py}")

    monkeypatch.chdir(package)
    _run_shell(f"{poetry} config --local virtualenvs.in-project true")
    _run_shell(f"{poetry} env use {py}")
    rc = _run_shell(f"{poetry} add {lib}")
    assert rc == 0
