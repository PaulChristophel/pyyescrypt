import os
import platform
import subprocess
import shutil
from pathlib import Path

from setuptools import setup
from setuptools.command.bdist_wheel import bdist_wheel as _bdist_wheel
from setuptools.command.build_py import build_py as _build_py

ROOT = Path(__file__).resolve().parent
PKG_NAME = "pyyescrypt"
NATIVE_SUBDIR = "_native"
CLI_SUBDIR = "_cli"


def _macos_target() -> str:
    """Return the configured macOS deployment target.

    Returns:
        str: Minimum supported macOS version.
    """
    return os.environ.get("MACOSX_DEPLOYMENT_TARGET", "12.0")


def _apply_macos_env(env: dict) -> None:
    """Configure Go's C compiler for the macOS deployment target.

    Args:
        env: Build environment to update in place.

    Returns:
        None.
    """
    if platform.system() != "Darwin":
        return
    target = _macos_target()
    env["MACOSX_DEPLOYMENT_TARGET"] = target
    flag = f"-mmacosx-version-min={target}"
    env.setdefault("CC", "clang")
    env.setdefault("CXX", "clang++")
    env["CGO_CFLAGS"] = " ".join(
        part for part in (env.get("CGO_CFLAGS", ""), flag) if part
    ).strip()
    env["CGO_LDFLAGS"] = " ".join(
        part for part in (env.get("CGO_LDFLAGS", ""), flag) if part
    ).strip()
    env["GO_LDFLAGS"] = " ".join(
        part
        for part in (env.get("GO_LDFLAGS", ""), f"-ldflags=-extldflags '{flag}'")
        if part
    ).strip()


def _go_exe() -> str:
    """Locate the configured Go toolchain.

    Returns:
        str: Path to the Go executable.

    Raises:
        RuntimeError: If Go cannot be found on PATH.
    """
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
    """Return the native library filename.

    Returns:
        str: Shared library filename for the build platform.
    """
    sysname = platform.system()
    if sysname == "Darwin":
        return "libyescrypt.dylib"
    if sysname == "Windows":
        return "yescrypt.dll"
    return "libyescrypt.so"


def _cli_filename() -> str:
    """Return the bundled CLI filename.

    Returns:
        str: Executable filename for the build platform.
    """
    return "pyyescrypt-cli.exe" if platform.system() == "Windows" else "pyyescrypt-cli"


def _build_native_to(dir_path: Path) -> None:
    """Build the Go shared library into a package directory.

    Args:
        dir_path: Destination for the native library.

    Returns:
        None.

    Raises:
        RuntimeError: If Go is unavailable.
        OSError: If creating the directory or starting Go fails.
        subprocess.CalledProcessError: If the build fails.
    """
    dir_path.mkdir(parents=True, exist_ok=True)
    out_path = dir_path / _lib_filename()

    go = _go_exe()
    env = os.environ.copy()
    env["CGO_ENABLED"] = "1"
    _apply_macos_env(env)
    subprocess.check_call(
        [
            go,
            "build",
            "-trimpath",
            "-ldflags=-w -s",
            "-buildmode=c-shared",
            "-o",
            str(out_path),
            "./capi",
        ],
        cwd=str(ROOT),
        env=env,
    )


def _build_cli_to(dir_path: Path) -> None:
    """Build the Go CLI into a package directory.

    Args:
        dir_path: Destination for the CLI executable.

    Returns:
        None.

    Raises:
        RuntimeError: If Go is unavailable.
        OSError: If creating the directory or starting Go fails.
        subprocess.CalledProcessError: If the build fails.
    """
    dir_path.mkdir(parents=True, exist_ok=True)
    out_path = dir_path / _cli_filename()

    go = _go_exe()
    env = os.environ.copy()
    _apply_macos_env(env)
    subprocess.check_call(
        [
            go,
            "build",
            "-trimpath",
            "-ldflags=-w -s",
            "-o",
            str(out_path),
            "./cmd/pyyescrypt-cli",
        ],
        cwd=str(ROOT),
        env=env,
    )


class build_py(_build_py):
    def run(self):
        """Build and package the Python modules and Go binaries.

        Returns:
            None.

        Raises:
            RuntimeError: If Go is unavailable.
            OSError: If file operations or starting Go fail.
            subprocess.CalledProcessError: If a Go build fails.
        """
        # Ensure native lib and CLI exist in src so setuptools packages them as data.
        src_native_dir = ROOT / "src" / PKG_NAME / NATIVE_SUBDIR
        src_cli_dir = ROOT / "src" / PKG_NAME / CLI_SUBDIR
        _build_native_to(src_native_dir)
        _build_cli_to(src_cli_dir)
        super().run()


class bdist_wheel(_bdist_wheel):
    """Package ctypes binaries without depending on a Python extension ABI."""

    def finalize_options(self):
        """Mark the wheel as platform dependent because it bundles Go binaries.

        Returns:
            None.
        """
        super().finalize_options()
        self.root_is_pure = False

    def get_tag(self):
        """Keep the native platform tag while removing Python ABI constraints.

        Returns:
            tuple[str, str, str]: Python, ABI, and platform compatibility tags.
        """
        _, _, platform_tag = super().get_tag()
        return "py3", "none", platform_tag


setup(
    cmdclass={"build_py": build_py, "bdist_wheel": bdist_wheel},
)
