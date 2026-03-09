all: lint test

include ../tools/python.mk

PIP_INSTALL := \
	--editable ../shared \
	--editable .[dev,sentry]
PYLINT_ARG := analyzer tests || true
MYPY_ARG := analyzer tests || true
BANDIT_ARG := analyzer || true

format: .format
lint: .format-check .pylint .mypy .bandit

fixtures:
	bash tests/fixtures/generate.sh

test: fixtures .pytest
test-coverage: fixtures .coverage
clean: .clean
