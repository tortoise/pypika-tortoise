checkfiles = pypika/ tests/ conftest.py
black_opts = -l 100 -t py38
py_warn = PYTHONDEVMODE=1

up:
	@poetry update

deps:
	@poetry install

check: deps _build _check
_check:
ifneq ($(shell which black),)
	black --check $(black_opts) $(checkfiles) || (echo "Please run 'make style' to auto-fix style issues" && false)
endif
	ruff check $(checkfiles)
	bandit -c pyproject.toml -r $(checkfiles)
	mypy $(checkfiles)
	twine check dist/*

test: deps _test
_test:
	$(py_warn) pytest

ci: deps _check _test

style: deps
	isort -src $(checkfiles)
	black $(black_opts) $(checkfiles)

build: deps _build
_build:
	rm -fR dist/
	poetry build

publish: deps _build
	twine upload dist/*
