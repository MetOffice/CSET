# © Crown copyright, Met Office (2022-2024) and CSET contributors.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Useful functions for the workflow."""

import json
from builtins import max, min, zip
from glob import glob

# Reexport functions for use within workflow.
__all__ = [
    "get_model_ids",
    "get_model_names",
    "get_models",
    "sanitise_task_name",
    # Reexported functions.
    "max",
    "min",
    "zip",
    "glob",
]


def get_models(rose_variables: dict) -> list[dict]:
    """Load per-model configuration into a single object.

    Returns a list of dictionaries, each one containing a per-model
    configuration.
    """
    models = []
    for model in range(1, 20):
        model_prefix = f"m{model}_"
        model_vars = {
            key.removeprefix(model_prefix): value
            for key, value in rose_variables.items()
            if key.startswith(model_prefix)
        }
        if model_vars:
            model_vars["id"] = model
            models.append(model_vars)
    return models


def get_model_names(models: list) -> str:
    """Get an JSON list literal of model names."""
    return json.dumps([model["name"] for model in models])


def get_model_ids(models: list) -> str:
    """Get space separated list of model identifiers."""
    return " ".join(str(model["id"]) for model in models)


def sanitise_task_name(s: str) -> str:
    """Sanitise a string to be used as a Cylc task name.

    Rules per
    https://cylc.github.io/cylc-doc/stable/html/user-guide/writing-workflows/runtime.html#cylc.flow.unicode_rules.TaskNameValidator
    The rules for valid task and family names:
        * must start with: alphanumeric
        * can only contain: alphanumeric, _, -, +, %, @
        * cannot start with: _cylc
        * cannot be: root

    Note that actually there are a few more characters supported, see:
    https://github.com/cylc/cylc-flow/issues/6288
    """
    # Ensure we have a string.
    if not isinstance(s, str):
        s = str(s)
    # Ensure the first character is alphanumeric.
    if not s[0].isalnum():
        s = f"sanitised_{s}"
    # Specifically replace `.` with `p`, as in 3p5.
    s = s.replace(".", "p")
    # Replace invalid characters with underscores.
    s = "".join(c if c.isalnum() or c in "-+%@" else "_" for c in s)
    # Ensure the name is not a reserved name.
    if s.lower() == "root":
        s = f"sanitised_{s}"
    # Ensure the name does not start with "_cylc".
    if s.lower().startswith("_cylc"):
        s = f"sanitised_{s}"
    return s
