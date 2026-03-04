SHELL := /bin/bash

PY ?= python3
GO ?= go
VENV ?= .venv
VENV_PY := $(VENV)/bin/python
VENV_PIP := $(VENV)/bin/pip

ROOT := $(CURDIR)
CAPIDIR := $(ROOT)/capi
PKG_NATIVE_DIR := $(ROOT)/src/pyyescrypt/_native
PKG_CLI_DIR := $(ROOT)/src/pyyescrypt/_cli

UNAME_S := $(shell uname -s)

ifeq ($(UNAME_S),Darwin)
	LIBNAME := libyescrypt.dylib
else ifeq ($(OS),Windows_NT)
	LIBNAME := yescrypt.dll
	EXEEXT := .exe
else
	LIBNAME := libyescrypt.so
endif

LIBOUT := $(PKG_NATIVE_DIR)/$(LIBNAME)
CLI_BIN := $(PKG_CLI_DIR)/pyyescrypt-cli$(EXEEXT)

.PHONY: all build native cli venv py-build py-sdist py-install py-editable test py-test fmt lint tidy upgrade clean distclean wheel-test

all: build

build: native cli py-build

venv:
	$(PY) -m venv "$(VENV)"
	"$(VENV_PY)" -m pip install -q --upgrade pip setuptools wheel

native:
	mkdir -p "$(PKG_NATIVE_DIR)"
	CGO_ENABLED=1 $(GO) build -buildmode=c-shared -o "$(LIBOUT)" "$(CAPIDIR)"

cli:
	mkdir -p "$(PKG_CLI_DIR)"
	$(GO) build -o "$(CLI_BIN)" "./cmd/pyyescrypt-cli"

py-build: venv
	"$(VENV_PY)" -m pip install -q --upgrade build
	"$(VENV_PY)" -m build --wheel

py-sdist: venv
	"$(VENV_PY)" -m pip install -q --upgrade build
	"$(VENV_PY)" -m build --sdist

py-install: venv
	"$(VENV_PIP)" install -q .

py-editable: venv
	"$(VENV_PIP)" install -q -e .

test: py-test wheel-test

py-test: native cli venv
	"$(VENV_PIP)" install -q --upgrade pytest
	"$(VENV_PIP)" install -q -e .
	"$(VENV_PY)" -m pytest -q

wheel-test: native cli venv
	"$(VENV_PY)" -m pip install -q --upgrade build
	"$(VENV_PY)" -m build --wheel
	"$(VENV_PIP)" install -q --force-reinstall dist/*.whl
	"$(VENV_PY)" -c 'import pathlib, pyyescrypt as m; p=pathlib.Path(m.__file__).resolve().parent/"_native"; ex=list(p.glob("*")); print(p); print(ex); assert ex, "no native library in package _native dir"'

fmt:
	$(GO) fmt ./...
	find . -type f -name '*py' -print0 | xargs -0 black

lint:
	golangci-lint run ./...

tidy:
	$(GO) mod tidy

upgrade:
	$(GO) get -u ./...
	$(GO) mod tidy

clean:
	find "$(ROOT)" -depth -type f -name '*.whl' -delete
	find "$(ROOT)" -depth -type f -name '*.so' -delete
	find "$(ROOT)" -depth -type f -name '*.dll' -delete
	find "$(ROOT)" -depth -type f -name '*.dylib' -delete
	find "$(ROOT)" -depth -type f -name '*.h' -delete
	find "$(ROOT)" -depth -type d -name '__pycache__' -ls -exec rm -rf {} \;
	find "$(ROOT)" -depth -type d -name 'pyyescrypt.egg-info' -ls -exec rm -rf {} \;
	find "$(ROOT)" -depth -maxdepth 1 -type d -name 'dist' -ls -exec rm -rf {} \;
	find "$(ROOT)" -depth -maxdepth 1 -type d -name 'build' -ls -exec rm -rf {} \;
	find "$(ROOT)" -depth -maxdepth 1 -type d -name '.venv' -ls -exec rm -rf {} \;
	find "$(ROOT)" -depth -maxdepth 1 -type d -name '.pytest_cache' -ls -exec rm -rf {} \;
	rm -rf "$(PKG_NATIVE_DIR)"
	rm -rf "$(PKG_CLI_DIR)"

# 	rm -rf "$(ROOT)/build"
# 	rm -rf "$(ROOT)/src/pyyescrypt.egg-info"
# 	rm -rf "$(ROOT)/src/pyyescrypt/*.so"
# 	rm -rf "$(ROOT)/tests/__pycache__"
# 	rm -rf "$(ROOT)/.pytest_cache"
# 	rm -rf "$(ROOT)/.venv"
# 	rm -rf "$(ROOT)/build"
# 	rm -rf "$(ROOT)/dist"
# 	rm -rf "$(PKG_NATIVE_DIR)/libyescrypt.dylib"
# 	rm -rf "$(PKG_NATIVE_DIR)/libyescrypt.dll"
# 	rm -rf "$(PKG_NATIVE_DIR)/libyescrypt.so"
# 	rm -rf "$(PKG_NATIVE_DIR)/libyescrypt.h"
