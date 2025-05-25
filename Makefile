src_dir = pypika_tortoise
checkfiles = $(src_dir) tests/ conftest.py
black_opts = -l 100 -t py39
py_warn = PYTHONDEVMODE=1
pytest_opts = -n auto --cov=$(src_dir) --cov-append --cov-branch --tb=native -q

up:
	@poetry update

deps:
	@poetry install

check: build _check
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
	$(py_warn) pytest $(pytest_opts)

ci: build _check _test

style: deps _style
_style:
	isort -src $(checkfiles)
	black $(black_opts) $(checkfiles)

lint: build
	isort -src $(checkfiles)
	black $(black_opts) $(checkfiles)
	ruff check --fix $(checkfiles)
	mypy $(checkfiles)
	bandit -c pyproject.toml -r $(checkfiles)
	twine check dist/*

build: deps
	poetry build --clean

publish: build
	twine upload dist/*
