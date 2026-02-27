import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _default_libname() -> str:
    if sys.platform == "darwin":
        return "libyescrypt.dylib"
    if sys.platform.startswith("win"):
        return "yescrypt.dll"
    return "libyescrypt.so"


def _repo_lib_path() -> Path:
    return ROOT / "src" / "pyyescrypt" / "_native" / _default_libname()


def _load_raw():
    import ctypes

    p = _repo_lib_path()
    if not p.exists():
        raise FileNotFoundError(
            f"native library not found at {p}. Run `make native` first."
        )

    lib = ctypes.CDLL(str(p))

    lib.yc_generate_hash.argtypes = [ctypes.c_char_p, ctypes.POINTER(ctypes.c_void_p)]
    lib.yc_generate_hash.restype = ctypes.c_void_p

    lib.yc_verify_hash.argtypes = [
        ctypes.c_char_p,
        ctypes.c_char_p,
        ctypes.POINTER(ctypes.c_int),
        ctypes.POINTER(ctypes.c_void_p),
    ]
    lib.yc_verify_hash.restype = ctypes.c_int

    lib.yc_free.argtypes = [ctypes.c_void_p]
    lib.yc_free.restype = None

    return lib


def _raise_if_err(lib, errp) -> None:
    import ctypes

    if errp and errp.value:
        msg = ctypes.string_at(errp.value).decode("utf-8", "replace")
        lib.yc_free(errp.value)
        raise ValueError(msg)


def _cstr(lib, ptr) -> str:
    import ctypes

    if not ptr:
        return ""
    s = ctypes.string_at(ptr).decode("utf-8", "replace")
    lib.yc_free(ptr)
    return s


def test_generate_hash_format() -> None:
    lib = _load_raw()
    import ctypes

    err = ctypes.c_void_p()
    ptr = lib.yc_generate_hash(b"correct horse battery staple", ctypes.byref(err))
    _raise_if_err(lib, err)
    assert ptr
    h = _cstr(lib, ptr)

    assert isinstance(h, str)
    assert h.startswith("$y$")
    assert h.count("$") >= 3
    assert re.match(r"^\$y\$.+\$.+$", h) is not None


def test_verify_hash_round_trip() -> None:
    lib = _load_raw()
    import ctypes

    pw = b"correct horse battery staple"

    err = ctypes.c_void_p()
    ptr = lib.yc_generate_hash(pw, ctypes.byref(err))
    _raise_if_err(lib, err)
    h = _cstr(lib, ptr).encode("utf-8")

    valid = ctypes.c_int(0)
    err = ctypes.c_void_p()
    ok = lib.yc_verify_hash(pw, h, ctypes.byref(valid), ctypes.byref(err))
    _raise_if_err(lib, err)
    assert ok == 1
    assert valid.value == 1

    valid = ctypes.c_int(0)
    err = ctypes.c_void_p()
    ok = lib.yc_verify_hash(b"nope", h, ctypes.byref(valid), ctypes.byref(err))
    _raise_if_err(lib, err)
    assert ok == 1
    assert valid.value == 0


def test_verify_hash_rejects_empty_hash() -> None:
    lib = _load_raw()
    import ctypes

    valid = ctypes.c_int(0)
    err = ctypes.c_void_p()
    ok = lib.yc_verify_hash(b"pw", b"", ctypes.byref(valid), ctypes.byref(err))
    assert ok == 0
    assert err.value


def test_verify_hash_rejects_bad_hash_string() -> None:
    lib = _load_raw()
    import ctypes

    valid = ctypes.c_int(0)
    err = ctypes.c_void_p()
    ok = lib.yc_verify_hash(
        b"pw",
        b"not-a-modular-crypt-hash",
        ctypes.byref(valid),
        ctypes.byref(err),
    )
    assert ok == 0
    assert err.value


def test_parallel_calls_smoke() -> None:
    lib = _load_raw()
    import concurrent.futures
    import ctypes

    def worker(i: int) -> bool:
        err = ctypes.c_void_p()
        pw = f"pw{i}".encode("utf-8")
        ptr = lib.yc_generate_hash(pw, ctypes.byref(err))
        _raise_if_err(lib, err)
        h = _cstr(lib, ptr).encode("utf-8")

        valid = ctypes.c_int(0)
        err = ctypes.c_void_p()
        ok = lib.yc_verify_hash(pw, h, ctypes.byref(valid), ctypes.byref(err))
        _raise_if_err(lib, err)
        return ok == 1 and valid.value == 1

    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as ex:
        results = list(ex.map(worker, range(50)))

    assert all(results)
