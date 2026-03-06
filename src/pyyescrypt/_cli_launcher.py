"""Console entry point that hands off to the bundled Go CLI."""

from __future__ import annotations

import os
import sys

from ._cli_backend import _cli_path


def main(argv: list[str] | None = None) -> int:
    """Exec the vendored binary so it behaves like the native CLI."""
    args = sys.argv[1:] if argv is None else list(argv)
    with _cli_path() as cli_path:
        os.execv(cli_path, [str(cli_path), *args])
    # os.execv never returns, but keep signature satisfy type checkers.
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
