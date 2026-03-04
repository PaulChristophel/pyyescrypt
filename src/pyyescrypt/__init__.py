"""
pyyescrypt public API.

A native Go shared library backend is used when available. On platforms where
the shared library cannot be loaded (for example musl-based systems), the
module automatically falls back to an included Go CLI that is invoked via
subprocess. Set ``PYYESCRYPT_BACKEND=cli`` or ``=native`` to force a backend.
"""

from __future__ import annotations

import os
import warnings
from types import ModuleType
from typing import Tuple

__all__ = ["generate_hash", "verify_hash"]


def _should_use_cli(exc: OSError) -> bool:
    msg = str(exc).lower()
    return "initial-exec tls" in msg or "musl" in msg


def _load_backend() -> Tuple[str, ModuleType]:
    forced = os.environ.get("PYYESCRYPT_BACKEND", "").strip().lower()
    if forced == "cli":
        from . import _cli_backend as backend

        return "cli", backend
    if forced == "native":
        from . import _native as backend

        return "native", backend

    try:
        from . import _native as backend

        return "native", backend
    except OSError as exc:
        if not _should_use_cli(exc):
            raise
        from . import _cli_backend as backend

        warnings.warn(
            "pyyescrypt native backend unavailable; falling back to CLI backend",
            RuntimeWarning,
            stacklevel=2,
        )
        return "cli", backend


_backend_name, _backend = _load_backend()
generate_hash = _backend.generate_hash
verify_hash = _backend.verify_hash
