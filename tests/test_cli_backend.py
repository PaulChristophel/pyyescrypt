import importlib
import sys

import pytest


@pytest.fixture
def cli_backend(monkeypatch):
    monkeypatch.setenv("PYYESCRYPT_BACKEND", "cli")
    sys.modules.pop("pyyescrypt", None)
    module = importlib.import_module("pyyescrypt")
    yield module
    sys.modules.pop("pyyescrypt", None)


def test_cli_round_trip(cli_backend):
    h = cli_backend.generate_hash("correct horse battery staple")
    assert h.startswith("$y$")
    assert cli_backend.verify_hash("correct horse battery staple", h) is True
    assert cli_backend.verify_hash("nope", h) is False
