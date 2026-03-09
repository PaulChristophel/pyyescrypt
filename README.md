# pyyescrypt

Python bindings for yescrypt, implemented as a small Go shared library loaded via `ctypes`.

No CPython C extension code. The Python package is pure Python, plus a platform-specific shared library:

- macOS: `libyescrypt.dylib`
- Linux (glibc): `libyescrypt.so`

Windows is currently unsupported because the Go-based build has only been
validated on macOS and glibc-based Linux.

## Public API

```python
import pyyescrypt

hash_str = pyyescrypt.generate_hash("my password")
ok = pyyescrypt.verify_hash("my password", hash_str)
```

- `generate_hash(password: str) -> str` returns a modular-crypt yescrypt hash string (typically starts with `$y$`).
- `verify_hash(password: str, hash_str: str) -> bool` verifies a password against a stored hash string.

Errors raised from the native layer become `ValueError` in Python.

## Command-line interface

Installing `pyyescrypt` also provides a `pyyescrypt-cli` executable (packaged Go binary). It exposes the same operations as the Python module:

```bash
# Generate a hash (reads the password from stdin)
printf "secret" | pyyescrypt-cli generate

# Verify returns exit status 0 on success and prints "1"
printf "secret" | pyyescrypt-cli verify --hash '$y$...'
```

The Python package automatically falls back to this CLI whenever the shared library cannot be loaded (for example on musl-based systems), and you can force it via `PYYESCRYPT_BACKEND=cli`.

## Repo layout

- `capi/` Go code compiled as a C-shared library (`-buildmode=c-shared`)
- `src/pyyescrypt/_native.py` loads the shared library with `ctypes` and exposes the Python API
- `src/pyyescrypt/_native/` destination directory for the built shared library
- `tests/` Python tests (ABI-level tests via `ctypes`)

## Requirements

- Go toolchain available on PATH
- Python 3.10+ required
- On macOS, Xcode Command Line Tools installed (`xcode-select --install`)

## Build the native library

```bash
make native
```

This builds the shared library into:

- `src/pyyescrypt/_native/libyescrypt.dylib` on macOS
- `src/pyyescrypt/_native/libyescrypt.so` on Linux

To build the bundled CLI (used automatically on musl) run:

```bash
make cli
```

which outputs `src/pyyescrypt/_cli/pyyescrypt-cli`.

## Run tests

```bash
make test
```

This will:
- run `go test -cover ./...`
- create a local virtualenv at `.venv`
- install test dependencies into the venv
- build the native library
- run `pytest`

If you want only the Python tests:

```bash
make py-test
```

## Development notes

### Why ctypes instead of a CPython extension
CPython extension modules require a C ABI boundary anyway. This project avoids the CPython C-API completely by exporting a small C ABI from Go and calling it from Python using `ctypes`.

### Memory ownership
Native functions return `char*` allocated by the native library. Python must free them by calling `yc_free`. The Python wrapper handles this.

### Linux libc notes
glibc-based distros (manylinux wheels) are fully supported today. Musl-based
systems such as Alpine cannot load the Go-built shared library because Go
currently emits `initial-exec` TLS relocations for `-buildmode=c-shared`, which
musl's dynamic loader refuses. Installing the wheel on Alpine succeeds, but the
native backend fails to import.

The package now ships a small Go CLI binary that the Python module falls back
to automatically whenever the native backend cannot be loaded (or when
`PYYESCRYPT_BACKEND=cli` is set). Set `PYYESCRYPT_BACKEND=native` if you prefer
to fail fast when the shared library is unavailable.

### Packaging
The wheel must include the shared library under `pyyescrypt/_native/`.

For local development, `make native` places the library in the repo tree where the tests expect it.

To validate packaging, use a separate workflow:
1) build a wheel
2) install it into a clean venv
3) import `pyyescrypt` and run the tests against the installed package data

## License
See `LICENSE`.
