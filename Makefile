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
	conda create -n cset-dev --file requirements/locks/py312-lock-linux-64.txt
	@echo "Run 'conda activate cset-dev' to use conda environment."

.git/hooks/pre-commit: conda
	conda run -n cset-dev pre-commit install

src/CSET/workflow/files/conda-environment:
	conda run -n cset-dev bash -euc 'ln -s "$CONDA_PREFIX" src/CSET/workflow/files/conda-environment'

setup: conda .git/hooks/pre-commit src/CSET/workflow/files/conda-environment ## Setup development environment.
	conda run -n cset-dev pip install --no-deps -e .

docs: ## Build documentation.
	cd docs && make html

pre-commit:
	pre-commit run --all-files

pytest:
	pytest -vv

test: pre-commit pytest ## Run linting and unit tests.

# Mark targets as 'phony' to indicate they don't actually produce a file with
# the same name as their target. Basically for actions rather than files.
.PHONY: help setup docs test
