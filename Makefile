# Lumint project Makefile
#
# Common developer entry points. All commands are run from the repo root.
# Windows (bash) users: invoke targets as `make target` (use `make` not
# `mingw32-make`). On Windows, ensure you have a POSIX-ish shell (Git Bash
# or WSL) and the project venv at backend/venv.

# Use bash explicitly (so recipes can rely on bash semantics on every OS).
SHELL := /usr/bin/env bash

# --- Project layout ---
BACKEND := backend
FRONTEND := frontend

# --- Python ---
PY := $(BACKEND)/venv/Scripts/python.exe
PIP := $(BACKEND)/venv/Scripts/pip.exe

# --- Tooling ---
.PHONY: help install lint typecheck test test-backend test-frontend build \
        smoke train-upi train-url eval clean

help:
	@echo "Lumint Makefile — common targets:"
	@echo "  make install        Install backend + frontend dependencies"
	@echo "  make lint           Run ruff on the backend"
	@echo "  make typecheck      Run mypy on the backend app"
	@echo "  make test           Run backend pytest + frontend lint/typecheck"
	@echo "  make test-backend   Run only the backend pytest suite"
	@echo "  make test-frontend  Run frontend lint/typecheck"
	@echo "  make build          Build frontend production bundle"
	@echo "  make smoke          Run end-to-end smoke test (starts uvicorn, curls probes)"
	@echo "  make eval           Run research evaluation harness"

install: install-backend install-frontend

install-backend:
	@echo "Installing backend deps..."
	cd $(BACKEND) && $(PIP) install -r requirements.txt

install-frontend:
	@echo "Installing frontend deps..."
	cd $(FRONTEND) && npm install

lint:
	cd $(BACKEND) && $(PY) -m ruff check .

typecheck:
	cd $(BACKEND) && $(PY) -m mypy app

test: test-backend test-frontend

test-backend:
	cd $(BACKEND) && $(PY) -m pytest -q

test-frontend:
	cd $(FRONTEND) && npm run test

build:
	cd $(FRONTEND) && npm run build

smoke:
	@echo "Running backend smoke test..."
	bash $(BACKEND)/scripts/smoke_test.sh

train-upi:
	cd $(BACKEND) && $(PY) ml/train.py --module upi

train-url:
	cd $(BACKEND) && $(PY) ml/train.py --module url

eval:
	cd $(BACKEND) && $(PY) ml/eval/run_eval.py

clean:
	find . -type d -name __pycache__ -prune -exec rm -rf {} +
	find . -type d -name .pytest_cache -prune -exec rm -rf {} +
	find . -type d -name .mypy_cache -prune -exec rm -rf {} +
	find . -type d -name .ruff_cache -prune -exec rm -rf {} +
