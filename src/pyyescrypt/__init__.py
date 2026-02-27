"""
pyyescrypt: small Python bindings for yescrypt.

Public API:
  - generate_hash(password: str) -> str
  - verify_hash(password: str, hash_str: str) -> bool
"""

from ._native import generate_hash, verify_hash

__all__ = ["generate_hash", "verify_hash"]
