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

import itertools
from builtins import max, min, zip
from glob import glob

# Reexport functions for use within workflow.
__all__ = [
    "get_models",
    "restructure_field_list",
    "sanitise_task_name",
    # Reexported functions.
    "max",
    "min",
    "zip",
    "glob",
]


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


def _batched(iterable, n):
    """Implement itertools.batched for Python < 3.12.

    batched('ABCDEFG', 3) → ABC DEF G
    https://docs.python.org/3/library/itertools.html#itertools.batched
    """
    if n < 1:
        raise ValueError("n must be at least one")
    iterator = iter(iterable)
    while batch := tuple(itertools.islice(iterator, n)):
        yield batch


def restructure_field_list(fields: list):
    """Restructure a 1D list of fields into a 2D list."""
    # ('m01s03i236', 'temp_at_screen_level', '', '', '', '', '', '', '', '',
    #  'm01s03i230', 'wind_speed_at_10m', '', '', '', '', '', '', '', '')
    # -> [{1: "m01s03i236", 2: "temp_at_screen_level"},
    #     {1: "m01s03i230", 2: "wind_speed_at_10m"}]
    max_number_of_models = 10
    assert len(fields) % max_number_of_models == 0
    # itertools.batched is from python 3.12
    batched = getattr(itertools, "batched", _batched)
    all_fields = batched(fields, max_number_of_models)
    rearranged = [
        {
            field[0] + 1: field[1]
            for field in enumerate(equivalent_model_fields)
            if field[1]
        }
        for equivalent_model_fields in all_fields
    ]
    return rearranged


def sanitise_task_name(s: str):
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
    # Ensure the first character is alphanumeric.
    if not s[0].isalnum():
        s = f"sanitised_{s}"
    # Replace invalid characters with underscores.
    s = "".join(c if c.isalnum() or c in "-+%@" else "_" for c in s)
    # Ensure the name is not a reserved name.
    if s.lower() == "root":
        s = f"sanitised_{s}"
    # Ensure the name does not start with "_cylc".
    if s.lower().startswith("_cylc"):
        s = f"sanitised_{s}"
    return s
