# Thin wrapper around tasks.py — requires make, but tasks.py works without it.
# On any platform without make: python tasks.py <command>

.PHONY: help setup dev-venv install run run-concurrent clean

PYTHON := $(shell python3 --version 2>/dev/null && echo python3 || echo python)

help:
	@$(PYTHON) tasks.py help

setup: dev-venv

dev-venv:
	$(PYTHON) tasks.py setup

install: dev-venv

run:
	$(PYTHON) tasks.py run $(ARGS)

run-concurrent:
	$(PYTHON) tasks.py run-concurrent

clean:
	$(PYTHON) tasks.py clean
