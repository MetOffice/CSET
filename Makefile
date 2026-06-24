# Makefile providing useful commands to assist with CSET development.
# See the make manual for more information:
# https://www.gnu.org/software/make/manual/html_node/

# To make a command appear in the help, provide a line of documentation after
# the target/prerequisites with ##.

# Use micromamba if available, else fall back to conda.
CONDA_EXE := $(shell command -v micromamba || echo "conda")

help: ## Display this help message.
	@echo "Please provide a target from:"
	@grep -E '^[a-zA-Z0-9_-]+:.*?## .*$$' $(MAKEFILE_LIST) \
	| sed -n 's/^\(.*:\) \(.*\)##\(.*\)/  \1\3/p'

# Check whether we are in the Met Office and modify lockfile if so.
prepare-lockfiles:
	@hostname -f | grep -qF metoffice \
	  && echo "Running on Met Office system; updating lockfiles to use conda-forge mirror." \
	  && sed -i "s|conda.anaconda.org|metoffice.jfrog.io/metoffice/api/conda|" requirements/locks/*.txt \
	  || true

conda: prepare-lockfiles
	${CONDA_EXE} create -n cset-dev --file requirements/locks/latest --yes
	git restore requirements/locks  # Reset lockfiles in case we Met Office'd them.

.git/hooks/pre-commit: conda
	${CONDA_EXE} run -n cset-dev pre-commit install

# Prevent pip from accessing the network; we have everything in our conda env.
setup: conda .git/hooks/pre-commit ## Setup development environment.
	${CONDA_EXE} run -n cset-dev pip install --no-deps --no-index --no-build-isolation --editable .
	@echo "Run '${CONDA_EXE} activate cset-dev' to use conda environment."

docs: ## Build documentation.
	make --directory=docs html

pre-commit:
	pre-commit run --all-files

test: pre-commit ## Run linting and unit tests.
	pytest -vv -m 'not slow'

test-fast: ## Run fast local tests only.
	pytest -vv --cov --cov-append --cov-config=pyproject.toml --numprocesses logical -m 'not slow and not network and not cylc'

test-workflow: ## Run workflow tests that require cylc.
	pytest -vv -m 'cylc'

test-full: pre-commit ## Run all tests, including slow or network reliant.
	# Install headless chromium for playwright browser tests.
	playwright install --only-shell chromium
	pytest -vv --cov --cov-append --cov-config=pyproject.toml --numprocesses logical

update-dev-deps:  ## Update pre-commit hooks and conda lock files for the development environment.
	scripts/update-developer-dependencies.sh

# Mark targets as 'phony' to indicate they don't actually produce a file with
# the same name as their target. Basically for actions rather than files.
.PHONY: help setup docs test test-fast test-workflow test-full prepare-lockfiles conda update-dev-deps
