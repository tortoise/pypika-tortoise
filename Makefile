src_dir = pypika_tortoise
checkfiles = $(src_dir) tests/ conftest.py
py_warn = PYTHONDEVMODE=1
pytest_opts = -n auto --cov=$(src_dir) --cov-append --cov-branch --tb=native -q

up:
	@poetry update

deps:
	poetry install --all-groups

typehints:
	mypy $(checkfiles)
	bandit -c pyproject.toml -r $(checkfiles)
	twine check dist/*

check: build _check
_check:
	ruff format --check $(checkfiles) || (echo "Please run 'make style' to auto-fix style issues" && false)
	ruff check $(checkfiles)
	$(MAKE) typehints

test: deps _test
_test:
	$(py_warn) pytest $(pytest_opts)

ci: build _check _test

style: deps _style
_style:
	ruff format $(checkfiles)
	ruff check --fix $(checkfiles)

lint: build _style
	$(MAKE) typehints

build: deps
	poetry build --clean

publish: build
	twine upload dist/*
