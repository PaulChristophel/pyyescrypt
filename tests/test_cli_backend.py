import importlib
import sys
import textwrap
from contextlib import contextmanager

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


def _setup_fake_cli_backend(monkeypatch, tmp_path, script_source):
    monkeypatch.setenv("PYYESCRYPT_BACKEND", "cli")
    for name in list(sys.modules):
        if name == "pyyescrypt" or name.startswith("pyyescrypt."):
            sys.modules.pop(name, None)
    cli_backend = importlib.import_module("pyyescrypt._cli_backend")
    cli_path = tmp_path / cli_backend.CLI_NAME
    cli_path.write_text(textwrap.dedent(script_source))
    cli_path.chmod(0o755)

    @contextmanager
    def fake_cli_path():
        yield cli_path

    monkeypatch.setattr(cli_backend, "_cli_path", fake_cli_path)
    return cli_backend


def test_generate_hash_invokes_cli_with_expected_args(monkeypatch, tmp_path):
    password = "correct horse battery staple"
    cli_backend = _setup_fake_cli_backend(
        monkeypatch,
        tmp_path,
        f"""#!/usr/bin/env python3
import sys

if sys.argv[1:] != [\"generate\"]:
    print(f\"unexpected args: {{sys.argv[1:]}}\", file=sys.stderr)
    sys.exit(5)

data = sys.stdin.read()
if data != {password!r}:
    print(\"unexpected password\", file=sys.stderr)
    sys.exit(6)

sys.stdout.write(\"stub-hash\\n\")
""",
    )

    assert cli_backend.generate_hash(password) == "stub-hash"


def test_verify_hash_interprets_cli_output(monkeypatch, tmp_path):
    cli_backend = _setup_fake_cli_backend(
        monkeypatch,
        tmp_path,
        """#!/usr/bin/env python3
import sys

if sys.argv[1:3] != [\"verify\", \"--hash\"]:
    print(\"bad args\", file=sys.stderr)
    sys.exit(7)

hash_value = sys.argv[3]
password = sys.stdin.read().strip()
if password == \"s3cr3t\" and hash_value == \"expected\":
    sys.stdout.write(\"1\\n\")
else:
    sys.stdout.write(\"0\\n\")
""",
    )

    assert cli_backend.verify_hash("s3cr3t", "expected") is True
    assert cli_backend.verify_hash("mismatch", "expected") is False


def test_generate_hash_raises_runtime_error_on_cli_failure(monkeypatch, tmp_path):
    cli_backend = _setup_fake_cli_backend(
        monkeypatch,
        tmp_path,
        """#!/usr/bin/env python3
import sys

print(\"simulated failure\", file=sys.stderr)
sys.exit(9)
""",
    )

    with pytest.raises(RuntimeError) as excinfo:
        cli_backend.generate_hash("pw")

    message = str(excinfo.value)
    assert "pyyescrypt CLI failed (9)" in message
    assert "simulated failure" in message
