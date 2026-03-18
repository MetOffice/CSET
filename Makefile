# Makefile providing useful commands to assist with CSET development.
# See the make manual for more information:
# https://www.gnu.org/software/make/manual/html_node/

# To make a command appear in the help, provide a line of documentation after
# the target/prerequisites with ##.

help: ## Display this help message.
	@echo "Please provide a target from:"
	@grep -E '^[a-zA-Z0-9_-]+:.*?## .*$$' $(MAKEFILE_LIST) \
	| sed -n 's/^\(.*:\) \(.*\)##\(.*\)/  \1\3/p'

conda:
	conda create -n cset-dev --file requirements/locks/latest
	@echo "Run 'conda activate cset-dev' to use conda environment."

.git/hooks/pre-commit: conda
	conda run -n cset-dev pre-commit install

setup: conda .git/hooks/pre-commit ## Setup development environment.
	conda run -n cset-dev pip install --no-deps -e .

docs: ## Build documentation.
	make --directory=docs html

pre-commit:
	pre-commit run --all-files

test: pre-commit ## Run linting and unit tests.
	pytest -vv -m 'not slow'

test-fast: ## Run fast local tests only.
	pytest -vv --cov --cov-append --cov-config=pyproject.toml --numprocesses logical -m 'not slow and not network'

test-full: pre-commit ## Run all tests, including slow or network reliant.
	pytest -vv --cov --cov-append --cov-config=pyproject.toml --numprocesses logical

# Mark targets as 'phony' to indicate they don't actually produce a file with
# the same name as their target. Basically for actions rather than files.
.PHONY: help setup docs test test-fast test-full
