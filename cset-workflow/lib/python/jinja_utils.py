"""Useful functions for the workflow."""

# Reexport some functions for use within workflow.
from builtins import zip  # noqa: F401
from glob import glob  # noqa: F401


def get_models(rose_variables: dict):
    """Load per-model configuration into a single object.

    Returns a list of dictionaries, each one containing a per-model
    configuration.
    """
    models = []
    for model in range(1, 11):
        model_prefix = f"m{model:02d}_"
        model_vars = {
            key.removeprefix(model_prefix): value
            for key, value in rose_variables.items()
            if key.startswith(model_prefix)
        }
        if model_vars:
            model_vars["number"] = model
            models.append(model_vars)
    return models
