import ctypes
import sys
from contextlib import contextmanager
from importlib import resources


def _default_libname() -> str:
    """Return the platform specific shared library filename.

    Returns:
        str: The expected filename for the native yescrypt shared library on the
        current platform.
    """
    if sys.platform == "darwin":
        return "libyescrypt.dylib"
    if sys.platform.startswith("win"):
        return "yescrypt.dll"
    return "libyescrypt.so"


def _load_lib() -> ctypes.CDLL:
    """Load the native yescrypt shared library using ctypes.

    Returns:
        ctypes.CDLL: A loaded handle to the native shared library.

    Raises:
        FileNotFoundError: If the shared library cannot be found inside the installed
        package data.
        OSError: If the dynamic loader fails to load the shared library.
    """
    libname = _default_libname()
    traversable = resources.files("pyyescrypt").joinpath("_native", libname)
    with resources.as_file(traversable) as lib_path:
        if not lib_path.exists():
            raise FileNotFoundError(f"native library not found: {lib_path}")
        return ctypes.CDLL(str(lib_path))


_lib = _load_lib()

_lib.yc_generate_hash.argtypes = [ctypes.c_void_p, ctypes.POINTER(ctypes.c_void_p)]
_lib.yc_generate_hash.restype = ctypes.c_void_p

_lib.yc_verify_hash.argtypes = [
    ctypes.c_void_p,
    ctypes.c_char_p,
    ctypes.POINTER(ctypes.c_int),
    ctypes.POINTER(ctypes.c_void_p),
]
_lib.yc_verify_hash.restype = ctypes.c_int

_lib.yc_free.argtypes = [ctypes.c_void_p]
_lib.yc_free.restype = None


@contextmanager
def _password_buffer(password: str):
    """Provide a writable NUL-terminated password buffer and scrub it on exit."""
    data = bytearray(password, "utf-8")
    data.append(0)
    buf = (ctypes.c_char * len(data)).from_buffer(data)
    try:
        yield ctypes.cast(buf, ctypes.c_void_p)
    finally:
        ctypes.memset(ctypes.addressof(buf), 0, len(data))


def _raise_if_err(err_ptr: ctypes.c_void_p) -> None:
    """Raise a Python exception if the native layer returned an error string.

    Args:
        err_ptr (ctypes.c_char_p): Pointer to a NUL terminated UTF 8 error string
        allocated by the native library, or NULL if no error occurred.

    Raises:
        ValueError: If err_ptr is non NULL, using the decoded native error message.
    """
    if err_ptr and err_ptr.value:
        msg = ctypes.string_at(err_ptr.value).decode("utf-8", "replace")
        _lib.yc_free(err_ptr.value)
        raise ValueError(msg)


def generate_hash(password: str) -> str:
    """Generate a yescrypt hash for a plaintext password.

    Args:
        password (str): Plaintext password to hash.

    Returns:
        str: Modular crypt formatted yescrypt hash string, typically starting with "$y$".

    Raises:
        ValueError: If the native layer reports an error.
        RuntimeError: If the native function returns NULL without an error.
    """
    err = ctypes.c_void_p()
    with _password_buffer(password) as password_buf:
        ptr = _lib.yc_generate_hash(password_buf, ctypes.byref(err))
    _raise_if_err(err)

    if not ptr:
        raise RuntimeError("yc_generate_hash returned null without error")

    try:
        return ctypes.string_at(ptr).decode("utf-8", "replace")
    finally:
        _lib.yc_free(ptr)


def verify_hash(password: str, hash_str: str) -> bool:
    """Verify a plaintext password against a stored yescrypt hash.

    Args:
        password (str): Plaintext password to verify.
        hash_str (str): Stored yescrypt hash string to verify against.

    Returns:
        bool: True if password matches hash_str, otherwise False.

    Raises:
        ValueError: If the native layer reports an error.
        RuntimeError: If the native function indicates failure without an error.
    """
    err = ctypes.c_void_p()
    valid = ctypes.c_int(0)

    with _password_buffer(password) as password_buf:
        ok = _lib.yc_verify_hash(
            password_buf,
            hash_str.encode("utf-8"),
            ctypes.byref(valid),
            ctypes.byref(err),
        )
    _raise_if_err(err)

    if ok != 1:
        raise RuntimeError("yc_verify_hash failed without error")

    return bool(valid.value)
