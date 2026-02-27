#!/bin/sh
set -eu

python - <<'PY'
import glob
import pathlib
import pyyescrypt

p = pathlib.Path(pyyescrypt.__file__).resolve().parent / "_native"
print("NATIVE_DIR=", p)
libs = sorted(glob.glob(str(p / "**/*.so"), recursive=True))
print("LIBS=", libs)
PY

python - <<'PY'
import glob
import pathlib
import pyyescrypt
import subprocess

p = pathlib.Path(pyyescrypt.__file__).resolve().parent / "_native"
libs = sorted(glob.glob(str(p / "**/*.so"), recursive=True))
for f in libs:
    print("FILE=", f)
    subprocess.run(["file", f], check=False)
    subprocess.run(["ldd", f], check=False)
PY
