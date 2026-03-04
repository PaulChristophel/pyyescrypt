"""CLI-based backend used when the native shared library cannot be loaded."""

from __future__ import annotations

import os
import subprocess
from contextlib import contextmanager
from importlib import resources
from pathlib import Path
from typing import Iterator, List

CLI_DIR = "_cli"
CLI_NAME = "pyyescrypt-cli.exe" if os.name == "nt" else "pyyescrypt-cli"


@contextmanager
def _cli_path() -> Iterator[Path]:
    traversable = resources.files("pyyescrypt").joinpath(CLI_DIR, CLI_NAME)
    if not traversable.exists():
        raise FileNotFoundError(f"pyyescrypt CLI not found at {traversable!s}")
    with resources.as_file(traversable) as path:
        yield path


def _run_cli(args: List[str], input_data: bytes) -> bytes:
    with _cli_path() as cli_path:
        proc = subprocess.run(
            [str(cli_path), *args],
            input=input_data,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
    if proc.returncode != 0:
        stderr = proc.stderr.decode("utf-8", "replace").strip()
        raise RuntimeError(f"pyyescrypt CLI failed ({proc.returncode}): {stderr}")
    return proc.stdout


def generate_hash(password: str) -> str:
    output = _run_cli(["generate"], password.encode("utf-8"))
    return output.decode("utf-8", "replace").strip()


def verify_hash(password: str, hash_str: str) -> bool:
    output = _run_cli(["verify", "--hash", hash_str], password.encode("utf-8"))
    text = output.decode("utf-8", "replace").strip()
    return text == "1"
