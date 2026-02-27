SHELL := /bin/bash

PY ?= python3
GO ?= go
VENV ?= .venv
VENV_PY := $(VENV)/bin/python
VENV_PIP := $(VENV)/bin/pip

ROOT := $(CURDIR)
CAPIDIR := $(ROOT)/capi
PKG_NATIVE_DIR := $(ROOT)/src/pyyescrypt/_native

UNAME_S := $(shell uname -s)

ifeq ($(UNAME_S),Darwin)
	LIBNAME := libyescrypt.dylib
else ifeq ($(OS),Windows_NT)
	LIBNAME := yescrypt.dll
else
	LIBNAME := libyescrypt.so
endif

LIBOUT := $(PKG_NATIVE_DIR)/$(LIBNAME)

.PHONY: all build native venv py-build py-sdist py-install py-editable test py-test fmt lint tidy upgrade clean distclean wheel-test

all: build

build: native py-build

venv:
	$(PY) -m venv "$(VENV)"
	"$(VENV_PY)" -m pip install -q --upgrade pip setuptools wheel

native:
	mkdir -p "$(PKG_NATIVE_DIR)"
	CGO_ENABLED=1 $(GO) build -buildmode=c-shared -o "$(LIBOUT)" "$(CAPIDIR)"

py-build:
	$(MAKE) venv
	"$(VENV_PY)" -m pip install -q --upgrade build
	"$(VENV_PY)" -m build --wheel

py-sdist:
	$(MAKE) venv
	"$(VENV_PY)" -m pip install -q --upgrade build
	"$(VENV_PY)" -m build --sdist

py-install:
	$(MAKE) venv
	"$(VENV_PIP)" install -q .

py-editable:
	$(MAKE) venv
	"$(VENV_PIP)" install -q -e .

test:
	$(MAKE) py-test

py-test: native venv
	"$(VENV_PIP)" install -q --upgrade pytest
	"$(VENV_PIP)" install -q -e .
	"$(VENV_PY)" -m pytest -q

wheel-test: clean venv
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
	rm -rf build dist *.egg-info
	rm -rf src/*.egg-info src/*/*.egg-info
	rm -rf "$(PKG_NATIVE_DIR)"
	rm -rf src/pyyescrypt/__pycache__
	rm -rf src/pyyescrypt/*.so
	rm -rf tests/__pycache__
	rm -rf .pytest_cache
	rm -rf .venv