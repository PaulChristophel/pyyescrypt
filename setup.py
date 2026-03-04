import os
import platform
import subprocess
import shutil
from pathlib import Path

from setuptools import Extension, setup
from setuptools.command.build_ext import build_ext as _build_ext
from setuptools.command.build_py import build_py as _build_py

ROOT = Path(__file__).resolve().parent
PKG_NAME = "pyyescrypt"
NATIVE_SUBDIR = "_native"
CLI_SUBDIR = "_cli"


def _macos_target() -> str:
    return os.environ.get("MACOSX_DEPLOYMENT_TARGET", "11.0")


def _apply_macos_env(env: dict) -> None:
    if platform.system() != "Darwin":
        return
    target = _macos_target()
    env["MACOSX_DEPLOYMENT_TARGET"] = target
    flag = f"-mmacosx-version-min={target}"
    env.setdefault("CC", "clang")
    env.setdefault("CXX", "clang++")
    env["CGO_CFLAGS"] = " ".join(part for part in (env.get("CGO_CFLAGS", ""), flag) if part).strip()
    env["CGO_LDFLAGS"] = " ".join(part for part in (env.get("CGO_LDFLAGS", ""), flag) if part).strip()


def _go_exe() -> str:
    # Allow callers (cibuildwheel, CI, local) to pin an absolute path.
    go = os.environ.get("GO", "go")
    if os.path.isabs(go):
        return go
    found = shutil.which(go)
    if not found:
        raise RuntimeError(
            f"Go toolchain not found on PATH (tried '{go}'). Set GO=/path/to/go or fix PATH."
        )
    return found


def _lib_filename() -> str:
    sysname = platform.system()
    if sysname == "Darwin":
        return "libyescrypt.dylib"
    if sysname == "Windows":
        return "yescrypt.dll"
    return "libyescrypt.so"


def _cli_filename() -> str:
    return "pyyescrypt-cli.exe" if platform.system() == "Windows" else "pyyescrypt-cli"


def _build_native_to(dir_path: Path) -> None:
    dir_path.mkdir(parents=True, exist_ok=True)
    out_path = dir_path / _lib_filename()

    go = _go_exe()
    env = os.environ.copy()
    env["CGO_ENABLED"] = "1"
    _apply_macos_env(env)
    subprocess.check_call(
        [go, "build", "-buildmode=c-shared", "-o", str(out_path), "./capi"],
        cwd=str(ROOT),
        env=env,
    )


def _build_cli_to(dir_path: Path) -> None:
    dir_path.mkdir(parents=True, exist_ok=True)
    out_path = dir_path / _cli_filename()

    go = _go_exe()
    env = os.environ.copy()
    _apply_macos_env(env)
    subprocess.check_call(
        [go, "build", "-o", str(out_path), "./cmd/pyyescrypt-cli"],
        cwd=str(ROOT),
        env=env,
    )


class build_py(_build_py):
    def run(self):
        # Ensure native lib and CLI exist in src so setuptools packages them as data.
        src_native_dir = ROOT / "src" / PKG_NAME / NATIVE_SUBDIR
        src_cli_dir = ROOT / "src" / PKG_NAME / CLI_SUBDIR
        _build_native_to(src_native_dir)
        _build_cli_to(src_cli_dir)
        super().run()


class build_ext(_build_ext):
    def run(self):
        # Only build the stub extension here. Native lib is built in build_py.
        super().run()


setup(
    ext_modules=[
        Extension(
            name="pyyescrypt._stub",
            sources=["stub.c"],
        )
    ],
    cmdclass={"build_py": build_py, "build_ext": build_ext},
)
