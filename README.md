# pyyescrypt

Python bindings for yescrypt, implemented as a small Go shared library loaded via `ctypes`.

No CPython C extension code. The Python package is pure Python, plus a platform-specific shared library:

- macOS: `libyescrypt.dylib`
- Linux: `libyescrypt.so`
- Windows: `yescrypt.dll`

## Public API

```python
import pyyescrypt

hash_str = pyyescrypt.generate_hash("my password")
ok = pyyescrypt.verify_hash("my password", hash_str)
```

- `generate_hash(password: str) -> str` returns a modular-crypt yescrypt hash string (typically starts with `$y$`).
- `verify_hash(password: str, hash_str: str) -> bool` verifies a password against a stored hash string.

Errors raised from the native layer become `ValueError` in Python.

## Repo layout

- `capi/` Go code compiled as a C-shared library (`-buildmode=c-shared`)
- `src/pyyescrypt/_native.py` loads the shared library with `ctypes` and exposes the Python API
- `src/pyyescrypt/_native/` destination directory for the built shared library
- `tests/` Python tests (ABI-level tests via `ctypes`)

## Requirements

- Go toolchain available on PATH
- Python 3.9+ recommended (package metadata says 3.9+)
- On macOS, Xcode Command Line Tools installed (`xcode-select --install`)

## Build the native library

```bash
make native
```

This builds the shared library into:

- `src/pyyescrypt/_native/libyescrypt.dylib` on macOS
- `src/pyyescrypt/_native/libyescrypt.so` on Linux
- `src/pyyescrypt/_native/yescrypt.dll` on Windows

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

### musl support (Alpine)
This approach works on musl if you compile the shared library against musl and build `musllinux` wheels.

Practical pattern:
- Build inside an Alpine container (or with a musl toolchain)
- Ensure `CGO_ENABLED=1` and `CC` points to a musl-capable compiler
- Produce a `musllinux_*` wheel containing the shared library

### Packaging
The wheel must include the shared library under `pyyescrypt/_native/`.

For local development, `make native` places the library in the repo tree where the tests expect it.

To validate packaging, use a separate workflow:
1) build a wheel
2) install it into a clean venv
3) import `pyyescrypt` and run the tests against the installed package data

## License
See `LICENSE`.
